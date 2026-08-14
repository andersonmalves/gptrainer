# Deterministic challenge runner

Use `scripts/runner.py` to compile and execute learner code against assistant-authored tests for Python, TypeScript, Java, or Kotlin.

## Safety boundary

The runner copies only the declared files into a disposable directory, uses a clean environment, applies a timeout, and applies basic resource limits where practical. It is **not a security sandbox**. It does not block network access, reads or writes outside the temp directory, or inherited `PATH` binaries. A timeout and a temp directory are not isolation. Run untrusted or adversarial code inside a container or VM instead.

Never run tests against production credentials, services, databases, or writable project data.

## Workflow

1. Run `doctor` to detect available toolchains.
2. Create a learner-owned solution file.
3. Create separate public and withheld test files. Clearly label them as assistant-authored.
4. Show public examples before the attempt. Do not reveal withheld test contents before scoring.
5. Run public tests during iteration.
6. Run withheld tests after the learner commits to an answer and records confidence.
7. Report only the failure class first if detailed output would expose the target insight.
8. Preserve the learner's code unchanged.

Withheld tests prevent accidental answer leakage; they are not secret from a user with filesystem access.

## Commands

```bash
python scripts/runner.py doctor

python scripts/runner.py run --language python \
  --solution solution.py --tests challenge_test.py --timeout 5

python scripts/runner.py run --language typescript \
  --solution solution.ts --tests challenge.test.ts --timeout 5

python scripts/runner.py run --language java \
  --solution Solution.java --tests ChallengeTest.java --entry ChallengeTest

python scripts/runner.py run --language kotlin \
  --solution Solution.kt --tests ChallengeTest.kt
```

Use repeatable `--support` arguments for additional source files. Use `--json` when another script consumes the result.

## Test conventions

Keep test harnesses dependency-free.

### Python

Import the solution, use plain assertions or `unittest`, and exit nonzero on failure:

```python
from solution import allocate

assert allocate(10, 2) == [5, 5]
print("PASS")
```

### TypeScript

Export from the solution and use a small dependency-free assertion function. Do not import Node type declarations because the runner intentionally requires only `tsc` and `node`:

```typescript
import { allocate } from "./solution";

function equal(actual: unknown, expected: unknown): void {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(`expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}

equal(allocate(10, 2), [5, 5]);
console.log("PASS");
```

### Java

Make the test filename match the public class containing `main`:

```java
public class ChallengeTest {
    public static void main(String[] args) {
        if (Solution.allocate(10, 2).size() != 2) {
            throw new AssertionError("unexpected allocation");
        }
        System.out.println("PASS");
    }
}
```

### Kotlin

Put one top-level `main` in the test file and use `check`:

```kotlin
fun main() {
    check(allocate(10, 2) == listOf(5, 5))
    println("PASS")
}
```

## Runtime requirements

| Language | Required commands |
|---|---|
| Python | `python3` |
| TypeScript | `tsc`, `node` |
| Java | `javac`, `java` |
| Kotlin | `kotlinc`, `java` |

If a toolchain is missing, state that limitation and use the project's existing test command if available. Do not silently replace deterministic execution with an LLM judgment.
