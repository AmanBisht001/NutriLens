import React, { useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  ScanLine,
  BookOpen,
  ArrowLeftRight,
  BookMarked,
  BarChart3,
  User,
  LogOut,
  Menu,
  X,
  ShieldCheck,
  ChevronRight,
  Sliders,
  Flag,
  Beaker,
  Package,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Scan Food", href: "/scan", icon: ScanLine },
  { name: "Food Catalogue", href: "/catalogue", icon: BookOpen },
  { name: "Compare Products", href: "/compare", icon: ArrowLeftRight },
  { name: "My Food Journal", href: "/journal", icon: BookMarked },
  { name: "Nutrition Analytics", href: "/analytics", icon: BarChart3 },
  { name: "My Profile", href: "/profile", icon: User },
];

const adminNavItems: NavItem[] = [
  { name: "Admin Overview", href: "/admin", icon: ShieldCheck },
  { name: "Product Management", href: "/admin/products", icon: Package },
  { name: "Ingredient Taxonomy", href: "/admin/ingredients", icon: Beaker },
  { name: "Scoring Engine Rules", href: "/admin/scoring-rules", icon: Sliders },
  { name: "Reported Issues", href: "/admin/issues", icon: Flag },
];

export const AppLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isAdmin = Boolean(
    user?.is_admin || user?.role === "admin" || user?.role === "superadmin"
  );

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const getInitials = (name?: string): string => {
    if (!name) return "NL";
    const parts = name.trim().split(" ");
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row">
      {/* Mobile Top Navigation Bar */}
      <div className="md:hidden flex items-center justify-between px-4 py-3 bg-white border-b sticky top-0 z-40">
        <Link to="/dashboard" className="flex items-center space-x-2">
          <div className="h-8 w-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <span className="font-bold text-foreground text-base">NutriLens</span>
        </Link>
        <button
          type="button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 rounded-md text-slate-600 hover:text-slate-900 hover:bg-slate-100"
          aria-label="Toggle navigation"
        >
          {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Mobile Drawer Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar Navigation */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 bg-white border-r flex flex-col justify-between transition-transform duration-300 ease-in-out md:static md:translate-x-0 ${
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex flex-col flex-1 overflow-y-auto">
          {/* Logo Header */}
          <div className="h-16 flex items-center px-6 border-b">
            <Link
              to="/dashboard"
              className="flex items-center space-x-2.5"
              onClick={() => setMobileMenuOpen(false)}
            >
              <div className="h-9 w-9 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-sm">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div className="flex flex-col">
                <span className="text-lg font-bold tracking-tight text-foreground">NutriLens</span>
                <span className="text-[10px] uppercase font-semibold text-muted-foreground tracking-wider">
                  Personal Food Intelligence
                </span>
              </div>
            </Link>
          </div>

          {/* User Quick Info */}
          <div className="px-5 py-4 border-b bg-slate-50/70">
            <div className="flex items-center space-x-3">
              <div className="h-10 w-10 rounded-full bg-emerald-100 border border-emerald-300 text-emerald-800 font-bold flex items-center justify-center text-sm shadow-sm">
                {getInitials(user?.full_name)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-slate-900 truncate">
                  {user?.full_name || "NutriLens Member"}
                </p>
                <p className="text-xs text-slate-500 truncate">{user?.email}</p>
              </div>
            </div>
            {user?.profile?.dietary_preference && user.profile.dietary_preference !== "None" && (
              <div className="mt-2.5 flex items-center gap-1.5 flex-wrap">
                <Badge variant="outline" className="text-[11px] bg-emerald-50 text-emerald-700 border-emerald-200">
                  {user.profile.dietary_preference}
                </Badge>
                {user.profile.allergies && user.profile.allergies.length > 0 && (
                  <Badge variant="secondary" className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200">
                    {user.profile.allergies.length} {user.profile.allergies.length === 1 ? "Allergy" : "Allergies"}
                  </Badge>
                )}
              </div>
            )}
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            <p className="px-3 pt-2 pb-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Main Menu
            </p>
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.href}
                  to={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-emerald-600 text-white shadow-sm"
                        : "text-slate-700 hover:bg-slate-100 hover:text-slate-900"
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <div className="flex items-center space-x-3">
                        <Icon
                          className={`h-4 w-4 ${
                            isActive ? "text-white" : "text-slate-500"
                          }`}
                        />
                        <span>{item.name}</span>
                      </div>
                      {isActive && <ChevronRight className="h-4 w-4 text-emerald-200" />}
                    </>
                  )}
                </NavLink>
              );
            })}

            {/* Admin Section */}
            {isAdmin && (
              <div className="pt-3 mt-2 border-t border-slate-100">
                <div className="px-3 pb-1.5 flex items-center justify-between">
                  <p className="text-[11px] font-semibold text-purple-600 uppercase tracking-wider">
                    Administration
                  </p>
                  <Badge variant="outline" className="text-[9px] bg-purple-50 text-purple-700 border-purple-200 px-1 py-0">
                    Admin
                  </Badge>
                </div>
                {adminNavItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.href}
                      to={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={({ isActive }) =>
                        `flex items-center justify-between px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                          isActive
                            ? "bg-purple-600 text-white shadow-sm"
                            : "text-slate-700 hover:bg-purple-50/70 hover:text-purple-900"
                        }`
                      }
                    >
                      {({ isActive }) => (
                        <>
                          <div className="flex items-center space-x-3">
                            <Icon
                              className={`h-4 w-4 ${
                                isActive ? "text-white" : "text-purple-500"
                              }`}
                            />
                            <span>{item.name}</span>
                          </div>
                          {isActive && <ChevronRight className="h-4 w-4 text-purple-200" />}
                        </>
                      )}
                    </NavLink>
                  );
                })}
              </div>
            )}
          </nav>
        </div>

        {/* Bottom Logout Button */}
        <div className="p-4 border-t bg-slate-50">
          <Button
            variant="outline"
            className="w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4 mr-2.5" />
            Sign Out
          </Button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 min-w-0 flex flex-col overflow-y-auto min-h-screen">
        <Outlet />
      </main>
    </div>
  );
};
