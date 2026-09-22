import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import ToBeRechecked from "./pages/ToBeRechecked";
import History from "./pages/History";

type Page = "dashboard" | "rechecked" | "history";

function App() {
  const [currentPage, setCurrentPage] = useState<Page>("dashboard");

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 p-6">
        <h1 className="text-xl font-bold text-gray-800 mb-8">
          Assessment Report Validator
        </h1>
        
        <nav className="space-y-2">
          <button
            onClick={() => setCurrentPage("dashboard")}
            className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
              currentPage === "dashboard"
                ? "bg-blue-50 text-blue-700 font-medium"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            Dashboard
          </button>
          
          <button
            onClick={() => setCurrentPage("rechecked")}
            className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
              currentPage === "rechecked"
                ? "bg-blue-50 text-blue-700 font-medium"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            To Be Re-checked
          </button>
          
          <button
            onClick={() => setCurrentPage("history")}
            className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
              currentPage === "history"
                ? "bg-blue-50 text-blue-700 font-medium"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            History
          </button>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8">
        {currentPage === "dashboard" && <Dashboard />}
        {currentPage === "rechecked" && <ToBeRechecked />}
        {currentPage === "history" && <History />}
      </main>
    </div>
  );
}

export default App;
