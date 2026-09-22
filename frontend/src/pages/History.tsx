import { useState, useEffect, useCallback } from "react";
import { getHistory } from "../services/api";
import type { HistoryResponse, HistoryRecord } from "../types/validation";
import FileDetailsDrawer from "../components/common/FileDetailsDrawer";

function History() {
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "PASS" | "ERROR" | "REVIEW">("ALL");
  const [selectedFile, setSelectedFile] = useState<HistoryRecord | null>(null);

  const loadHistory = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getHistory();
      setHistory(data);
      setError(null);
    } catch (err) {
      console.error("Failed to load history:", err);
      setError("Failed to load history");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const filteredHistory = history?.history.filter((record) => {
    const matchesSearch = record.filename.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "ALL" || record.status === statusFilter;
    return matchesSearch && matchesStatus;
  }) || [];

  if (loading) {
    return <div className="text-gray-600">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-600">{error}</div>;
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">History</h2>

      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6 flex items-center gap-4">
        <input
          type="text"
          placeholder="Search by filename..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as any)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="ALL">All Status</option>
          <option value="PASS">PASS</option>
          <option value="ERROR">ERROR</option>
          <option value="REVIEW">REVIEW</option>
        </select>
      </div>

      <div className="text-sm text-gray-600 mb-4">
        Showing {filteredHistory.length} of {history?.total || 0} records
      </div>

      {filteredHistory.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-600">
          No history records found.
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-6 py-3 text-sm font-semibold text-gray-700">Filename</th>
                <th className="text-left px-6 py-3 text-sm font-semibold text-gray-700">Date</th>
                <th className="text-left px-6 py-3 text-sm font-semibold text-gray-700">Status</th>
                <th className="text-left px-6 py-3 text-sm font-semibold text-gray-700">Issues</th>
                <th className="text-left px-6 py-3 text-sm font-semibold text-gray-700">Review State</th>
                <th className="text-left px-6 py-3 text-sm font-semibold text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredHistory.map((record, index) => (
                <tr key={`${record.filename}-${index}`} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm text-gray-800">{record.filename}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{new Date(record.timestamp).toLocaleString()}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      record.status === "PASS" ? "bg-green-100 text-green-700" :
                      record.status === "ERROR" ? "bg-red-100 text-red-700" :
                      "bg-yellow-100 text-yellow-700"
                    }`}>
                      {record.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {record.error_count} errors, {record.review_count} review
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      record.review_state === "VERIFIED" ? "bg-green-100 text-green-700" :
                      record.review_state === "INCORRECT" ? "bg-red-100 text-red-700" :
                      "bg-gray-100 text-gray-700"
                    }`}>
                      {record.review_state}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => setSelectedFile(record)}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selectedFile && (
        <FileDetailsDrawer
          file={selectedFile}
          onClose={() => setSelectedFile(null)}
          showReviewActions={false}
        />
      )}
    </div>
  );
}

export default History;
