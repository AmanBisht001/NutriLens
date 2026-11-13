import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Flag,
  CheckCircle2,
  Clock,
  XCircle,
  ChevronLeft,
  ExternalLink,
  Loader2,
  AlertTriangle,
  MessageSquare,
} from "lucide-react";
import { api } from "@/services/api";
import { ProductIssueItem } from "@/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

export const AdminIssuesPage: React.FC = () => {
  const [issues, setIssues] = useState<ProductIssueItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("pending");
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Resolution modal state
  const [selectedIssue, setSelectedIssue] = useState<ProductIssueItem | null>(null);
  const [resolveForm, setResolveForm] = useState<{
    status: "pending" | "reviewed" | "resolved" | "rejected";
    admin_notes: string;
  }>({
    status: "resolved",
    admin_notes: "",
  });

  const fetchIssues = async () => {
    try {
      setLoading(true);
      const data = await api.getAdminIssues(statusFilter === "all" ? undefined : statusFilter);
      setIssues(data);
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to load reported issues.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIssues();
  }, [statusFilter]);

  const openResolveModal = (issue: ProductIssueItem) => {
    setSelectedIssue(issue);
    setResolveForm({
      status: issue.status === "pending" ? "resolved" : issue.status,
      admin_notes: issue.admin_notes || "",
    });
  };

  const handleResolveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIssue) return;

    try {
      setActionLoading("resolving");
      const updated = await api.updateAdminIssue(selectedIssue.id, {
        status: resolveForm.status,
        admin_notes: resolveForm.admin_notes.trim() || undefined,
      });

      setIssues((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      setSelectedIssue(null);
      alert(`Issue #${updated.id.slice(0, 8)} updated to status: ${updated.status}.`);
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to update issue status.");
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "resolved":
        return <Badge className="bg-emerald-600 text-white text-[10px]"><CheckCircle2 className="h-3 w-3 mr-1" /> Resolved</Badge>;
      case "reviewed":
        return <Badge className="bg-blue-600 text-white text-[10px]"><Clock className="h-3 w-3 mr-1" /> Under Review</Badge>;
      case "rejected":
        return <Badge variant="outline" className="text-slate-500 bg-slate-100 text-[10px]"><XCircle className="h-3 w-3 mr-1" /> Rejected</Badge>;
      default:
        return <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-300 text-[10px]"><AlertTriangle className="h-3 w-3 mr-1" /> Pending</Badge>;
    }
  };

  const formatIssueType = (t: string) => {
    return t.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  };

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <Link to="/admin" className="text-xs text-purple-600 hover:underline font-semibold flex items-center">
              <ChevronLeft className="h-3 w-3 mr-0.5" /> Admin Dashboard
            </Link>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">User Reported Data Issues</h1>
          <p className="text-slate-500 text-xs mt-0.5">
            Audit user-flagged inaccuracies in food labels, OCR omissions, and incorrect nutritional facts.
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-lg text-xs">
          {["pending", "reviewed", "resolved", "rejected", "all"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-md font-medium capitalize transition-colors ${
                statusFilter === st
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Issues Queue Table */}
      <Card className="border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b text-xs uppercase font-semibold text-slate-500">
              <tr>
                <th className="py-3 px-4">Product</th>
                <th className="py-3 px-4">Issue Type</th>
                <th className="py-3 px-4">User Notes & Details</th>
                <th className="py-3 px-4">Submitted</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2 text-indigo-600" />
                    Loading reported issues...
                  </td>
                </tr>
              ) : issues.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    No data issues found in the "{statusFilter}" queue.
                  </td>
                </tr>
              ) : (
                issues.map((issue) => (
                  <tr key={issue.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900">{issue.product_name || "Packaged Product"}</div>
                      {issue.product_brand && (
                        <div className="text-xs text-slate-400">{issue.product_brand}</div>
                      )}
                      <Link
                        to={`/catalogue/${issue.product_id}`}
                        target="_blank"
                        className="text-[11px] text-emerald-600 hover:underline flex items-center gap-0.5 mt-0.5"
                      >
                        Inspect Product <ExternalLink className="h-3 w-3" />
                      </Link>
                    </td>
                    <td className="py-3 px-4">
                      <Badge variant="outline" className="bg-indigo-50 text-indigo-700 border-indigo-200 text-xs">
                        {formatIssueType(issue.issue_type)}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 max-w-md">
                      <p className="text-xs text-slate-800 line-clamp-2">{issue.description}</p>
                      {issue.admin_notes && (
                        <p className="text-[11px] text-slate-500 mt-1 italic">
                          Admin note: {issue.admin_notes}
                        </p>
                      )}
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-400 whitespace-nowrap">
                      {new Date(issue.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-center">{getStatusBadge(issue.status)}</td>
                    <td className="py-3 px-4 text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => openResolveModal(issue)}
                        className="text-xs h-8 border-slate-300 hover:bg-slate-50"
                      >
                        <MessageSquare className="h-3.5 w-3.5 mr-1" /> Audit
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Review / Resolve Modal */}
      {selectedIssue && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden">
            <div className="px-6 py-4 border-b flex items-center justify-between bg-slate-50">
              <div className="flex items-center space-x-2">
                <Flag className="h-5 w-5 text-indigo-600" />
                <h2 className="text-base font-bold text-slate-900">Audit Reported Issue</h2>
              </div>
              <button
                type="button"
                onClick={() => setSelectedIssue(null)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleResolveSubmit} className="p-6 space-y-4 text-xs">
              <div className="p-3 bg-slate-50 rounded-lg border space-y-1">
                <div className="flex justify-between">
                  <span className="font-semibold text-slate-500 uppercase text-[10px]">Product</span>
                  <span className="font-bold text-slate-900">{selectedIssue.product_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-semibold text-slate-500 uppercase text-[10px]">Reported Category</span>
                  <span className="font-medium text-slate-700">{formatIssueType(selectedIssue.issue_type)}</span>
                </div>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">User Reported Problem:</label>
                <div className="p-3 bg-slate-50 border rounded-md text-slate-800 leading-relaxed text-xs">
                  {selectedIssue.description}
                </div>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Update Resolution Status</label>
                <select
                  value={resolveForm.status}
                  onChange={(e: any) => setResolveForm({ ...resolveForm, status: e.target.value })}
                  className="h-9 w-full px-3 rounded-md border border-input bg-background text-xs font-semibold"
                >
                  <option value="pending">Pending (Awaiting investigation)</option>
                  <option value="reviewed">Under Review (Checked by editorial)</option>
                  <option value="resolved">Resolved (Corrections applied to database)</option>
                  <option value="rejected">Rejected (Report invalid or duplicate)</option>
                </select>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  Resolution Notes & Audit Log (Optional)
                </label>
                <textarea
                  rows={3}
                  value={resolveForm.admin_notes}
                  onChange={(e) => setResolveForm({ ...resolveForm, admin_notes: e.target.value })}
                  placeholder="e.g. Corrected sodium value to 350mg based on official packaging photo..."
                  className="w-full p-2 border rounded-md text-xs focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="pt-4 border-t flex justify-end gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => setSelectedIssue(null)}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={actionLoading === "resolving"}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white"
                >
                  {actionLoading === "resolving" ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-1.5" />
                  ) : null}
                  Save Resolution
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
