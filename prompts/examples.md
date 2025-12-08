# Sui Application Examples

Examples of building applications with Sui (logic) + UI (any framework).

---

## Full Application Examples

### Example: Counter App

**Prompt:**
```
Create a counter app with increment and decrement buttons
```

**Expected Output:**

**logic.sui**
```sui
= g0 0

# 0 0 {
  + g0 g0 1
  ^ 0
}

# 1 0 {
  - g0 g0 1
  ^ 0
}
```

**ui.html**
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Counter</title>
  <style>
    body { font-family: system-ui; text-align: center; padding: 2rem; }
    button { font-size: 1.5rem; margin: 0.5rem; padding: 0.5rem 1rem; }
    #count { font-size: 3rem; margin: 1rem; }
  </style>
</head>
<body>
  <div id="count">0</div>
  <button id="dec">−</button>
  <button id="inc">+</button>
  <script type="module">
    const wasmBytes = await fetch('logic.wasm').then(r => r.arrayBuffer());
    const { instance } = await WebAssembly.instantiate(wasmBytes, { env: { print_i32: console.log } });
    const { f0, f1, g0 } = instance.exports;
    const update = () => document.getElementById('count').textContent = g0.value;
    document.getElementById('inc').onclick = () => { f0(); update(); };
    document.getElementById('dec').onclick = () => { f1(); update(); };
    update();
  </script>
</body>
</html>
```

---

### Example: Calculator App

**Prompt:**
```
Create a simple calculator with add, subtract, multiply, divide (React)
```

**Expected Output:**

**logic.sui**
```sui
= g0 0
= g1 0
= g2 0

# 0 0 { + g2 g0 g1 ^ 0 }
# 1 0 { - g2 g0 g1 ^ 0 }
# 2 0 { * g2 g0 g1 ^ 0 }
# 3 0 { / g2 g0 g1 ^ 0 }
```

**Calculator.jsx**
```jsx
import { useState } from 'react';

export function Calculator({ wasm }) {
  const [a, setA] = useState(0);
  const [b, setB] = useState(0);
  const [result, setResult] = useState(0);

  const calc = (fn) => {
    wasm.exports.g0.value = a;
    wasm.exports.g1.value = b;
    wasm.exports[fn]();
    setResult(wasm.exports.g2.value);
  };

  return (
    <div>
      <input type="number" value={a} onChange={e => setA(+e.target.value)} />
      <input type="number" value={b} onChange={e => setB(+e.target.value)} />
      <div>
        <button onClick={() => calc('f0')}>+</button>
        <button onClick={() => calc('f1')}>−</button>
        <button onClick={() => calc('f2')}>×</button>
        <button onClick={() => calc('f3')}>÷</button>
      </div>
      <div>Result: {result}</div>
    </div>
  );
}
```

---

### Example: Todo List App

**Prompt:**
```
Create a todo list with add and toggle complete (vanilla JS)
```

**Expected Output:**

**logic.sui**
```sui
[ g0 100
= g1 0

# 0 0 {
  { g0 g1 0
  + g1 g1 1
  ^ 0
}

# 1 1 {
  ] v0 g0 a0
  ! v1 v0
  { g0 a0 v1
  ^ 0
}
```

**ui.html**
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Todo</title>
  <style>
    body { font-family: system-ui; max-width: 400px; margin: 2rem auto; }
    .done { text-decoration: line-through; opacity: 0.5; }
    li { cursor: pointer; padding: 0.5rem; }
  </style>
</head>
<body>
  <input id="input" placeholder="New todo">
  <button id="add">Add</button>
  <ul id="list"></ul>
  <script type="module">
    const wasmBytes = await fetch('logic.wasm').then(r => r.arrayBuffer());
    const { instance } = await WebAssembly.instantiate(wasmBytes, { env: { print_i32: console.log } });
    const { f0, f1, g0, g1 } = instance.exports;
    
    const todos = [];
    const list = document.getElementById('list');
    
    const render = () => {
      list.innerHTML = todos.map((t, i) => 
        `<li class="${g0.value ? 'done' : ''}" data-i="${i}">${t}</li>`
      ).join('');
    };
    
    document.getElementById('add').onclick = () => {
      const input = document.getElementById('input');
      if (input.value) {
        todos.push(input.value);
        f0();
        input.value = '';
        render();
      }
    };
    
    list.onclick = (e) => {
      if (e.target.tagName === 'LI') {
        f1(+e.target.dataset.i);
        render();
      }
    };
  </script>
</body>
</html>
```

---

## Pure Logic Examples (Sui only)

### Example 1: Simple Loop

**Prompt:**
```
Generate Sui code that prints numbers from 1 to 10
```

**Expected Output:**
```sui
= v0 1
: 0
> v1 v0 10
? v1 1
. v0
+ v0 v0 1
@ 0
: 1
```

---

### Example 2: Sum of Array

**Prompt:**
```
Generate Sui code that creates an array [1,2,3,4,5] and calculates the sum
```

**Expected Output:**
```sui
[ g0 5
{ g0 0 1
{ g0 1 2
{ g0 2 3
{ g0 3 4
{ g0 4 5
= g1 0
= v0 0
: 0
< v1 v0 5
! v2 v1
? v2 1
] v3 g0 v0
+ g1 g1 v3
+ v0 v0 1
@ 0
: 1
. g1
```

---

### Example 3: Factorial

**Prompt:**
```
Generate Sui code for factorial function and calculate 5!
```

**Expected Output:**
```sui
# 0 1 {
< v0 a0 2
! v1 v0
? v1 1
^ 1
: 1
- v2 a0 1
$ v3 0 v2
* v4 a0 v3
^ v4
}
= g0 5
$ g1 0 g0
. g1
```

---

### Example 4: Fibonacci

**Prompt:**
```
Generate Sui code for fibonacci function and print fib(10)
```

**Expected Output:**
```sui
# 0 1 {
< v0 a0 2
! v1 v0
? v1 1
^ a0
: 1
- v2 a0 1
$ v3 0 v2
- v4 a0 2
$ v5 0 v4
+ v6 v3 v5
^ v6
}
= g0 10
$ g1 0 g0
. g1
```

---

### Example 5: FizzBuzz

**Prompt:**
```
Generate Sui code for FizzBuzz from 1 to 100
```

**Expected Output:**
```sui
= v0 1
: 0
> v1 v0 100
? v1 1
% v2 v0 15
~ v3 v2 0
? v3 2
% v4 v0 3
~ v5 v4 0
? v5 3
% v6 v0 5
~ v7 v6 0
? v7 4
. v0
@ 5
: 2
. "FizzBuzz"
@ 5
: 3
. "Fizz"
@ 5
: 4
. "Buzz"
: 5
+ v0 v0 1
@ 0
: 1
```

---

### Example 6: Prime Check

**Prompt:**
```
Generate Sui code that checks if a number is prime
```

**Expected Output:**
```sui
# 0 1 {
< v0 a0 2
? v0 1
= v1 2
: 0
* v2 v1 v1
> v3 v2 a0
? v3 2
% v4 a0 v1
~ v5 v4 0
? v5 1
+ v1 v1 1
@ 0
: 2
^ 1
: 1
^ 0
}
= g0 17
$ g1 0 g0
. g1
```

---

### Example 7: Bubble Sort

**Prompt:**
```
Generate Sui code for bubble sort on an array of 5 elements
```

**Expected Output:**
```sui
[ g0 5
{ g0 0 5
{ g0 1 2
{ g0 2 8
{ g0 3 1
{ g0 4 9
= v0 5
- v0 v0 1
: 0
< v1 v0 1
? v1 3
= v2 0
: 1
< v3 v2 v0
! v4 v3
? v4 2
] v5 g0 v2
+ v6 v2 1
] v7 g0 v6
> v8 v5 v7
! v9 v8
? v9 4
{ g0 v2 v7
{ g0 v6 v5
: 4
+ v2 v2 1
@ 1
: 2
- v0 v0 1
@ 0
: 3
= v0 0
: 5
< v1 v0 5
! v2 v1
? v2 6
] v3 g0 v0
. v3
+ v0 v0 1
@ 5
: 6
```

---

---

## Common Patterns

### Loop Pattern
```sui
; for i in range(n)
= v0 0
: start_label
< v1 v0 n
! v2 v1
? v2 end_label
[body using v0 as i]
+ v0 v0 1
@ start_label
: end_label
```

### Function Pattern
```sui
; def func(arg):
;     return result
# func_id arg_count {
[body]
^ result
}
```

### Conditional Pattern
```sui
; if condition:
;     then_block
; else:
;     else_block
[compute condition into v0]
? v0 else_label
[then_block]
@ end_label
: else_label
[else_block]
: end_label
```

### While Loop Pattern
```sui
; while condition:
;     body
: loop_start
[compute condition into v0]
! v1 v0
? v1 loop_end
[body]
@ loop_start
: loop_end
```
