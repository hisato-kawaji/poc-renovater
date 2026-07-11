"use client";
import { useState } from "react";

export default function Home() {
  const [todos, setTodos] = useState<{id: number, text: string, done: boolean}[]>([]);
  const [text, setText] = useState("");

  const addTodo = () => {
    if (!text.trim()) return;
    setTodos([...todos, { id: Date.now(), text, done: false }]);
    setText("");
  };

  const toggleTodo = (id: number) => {
    setTodos(todos.map(t => t.id === id ? { ...t, done: !t.done } : t));
  };

  const deleteTodo = (id: number) => {
    setTodos(todos.filter(t => t.id !== id));
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-lg p-6 w-full max-w-md">
        <h1 className="text-2xl font-bold text-gray-800 mb-6 text-center">PoC Renovater Test App</h1>
        
        <div className="flex gap-2 mb-6">
          <input
            type="text"
            className="flex-1 border rounded px-3 py-2 outline-none focus:border-blue-500"
            placeholder="Add a new task..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addTodo()}
          />
          <button
            onClick={addTodo}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 font-medium"
          >
            Add
          </button>
        </div>

        <ul className="space-y-3">
          {todos.length === 0 ? (
            <p className="text-center text-gray-500 py-4">No tasks yet.</p>
          ) : (
            todos.map(todo => (
              <li key={todo.id} className="flex items-center justify-between p-3 border rounded hover:bg-gray-50 transition-colors">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={todo.done}
                    onChange={() => toggleTodo(todo.id)}
                    className="w-5 h-5 cursor-pointer accent-blue-600"
                  />
                  <span className={`text-gray-800 ${todo.done ? "line-through text-gray-400" : ""}`}>
                    {todo.text}
                  </span>
                </div>
                <button
                  onClick={() => deleteTodo(todo.id)}
                  className="text-red-500 hover:text-red-700 p-1"
                >
                  ✕
                </button>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
}
