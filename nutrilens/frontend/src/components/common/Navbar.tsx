import React from "react";
import { Link, useLocation } from "react-router-dom";
import { ShieldCheck, LayoutDashboard, LogIn, UserPlus, User } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";

export const Navbar: React.FC = () => {
  const location = useLocation();
  const { isAuthenticated, user } = useAuth();

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <Link to="/" className="flex items-center space-x-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600 text-white shadow-sm">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-bold tracking-tight text-foreground">NutriLens</span>
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
              Food Intelligence
            </span>
          </div>
        </Link>

        <nav className="hidden md:flex items-center space-x-6 text-sm font-medium">
          <Link
            to="/"
            className={`transition-colors hover:text-emerald-600 ${
              location.pathname === "/" ? "text-emerald-600 font-semibold" : "text-muted-foreground"
            }`}
          >
            Overview
          </Link>
          <a
            href="#architecture"
            className="text-muted-foreground transition-colors hover:text-emerald-600"
          >
            Architecture
          </a>
          <a
            href="#status"
            className="text-muted-foreground transition-colors hover:text-emerald-600"
          >
            System Status
          </a>
          {isAuthenticated && (
            <Link
              to="/dashboard"
              className="text-emerald-700 font-semibold transition-colors hover:text-emerald-800"
            >
              Dashboard
            </Link>
          )}
        </nav>

        <div className="flex items-center space-x-2.5">
          {isAuthenticated ? (
            <div className="flex items-center space-x-2">
              <Button asChild variant="outline" size="sm" className="hidden sm:inline-flex">
                <Link to="/profile">
                  <User className="h-4 w-4 mr-1.5 text-emerald-600" />
                  {user?.full_name?.split(" ")[0] || "Profile"}
                </Link>
              </Button>
              <Button asChild size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white">
                <Link to="/dashboard">
                  <LayoutDashboard className="h-4 w-4 mr-1.5" />
                  Dashboard
                </Link>
              </Button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <Button asChild variant="ghost" size="sm">
                <Link to="/login">
                  <LogIn className="h-4 w-4 mr-1.5" />
                  Sign In
                </Link>
              </Button>
              <Button asChild size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white">
                <Link to="/register">
                  <UserPlus className="h-4 w-4 mr-1.5" />
                  Get Started
                </Link>
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
