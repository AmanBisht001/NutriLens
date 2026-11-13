import React from "react";
import { ShieldCheck, Heart } from "lucide-react";

export const Footer: React.FC = () => {
  return (
    <footer className="border-t bg-muted/30 py-8 text-sm">
      <div className="container flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-2 text-muted-foreground">
          <ShieldCheck className="h-4 w-4 text-emerald-600" />
          <span>NutriLens – Final-Year B.Tech Major Project</span>
        </div>
        <div className="flex items-center space-x-1 text-xs text-muted-foreground">
          <span>Engineered with explainable rules, FastAPI, React & PostgreSQL</span>
          <span>•</span>
          <span className="flex items-center gap-1">
            Built with <Heart className="h-3 w-3 text-red-500 fill-red-500" /> for transparent nutrition
          </span>
        </div>
      </div>
    </footer>
  );
};
