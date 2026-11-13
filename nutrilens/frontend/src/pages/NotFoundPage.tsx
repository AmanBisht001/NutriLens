import React from "react";
import { Link } from "react-router-dom";
import { AlertCircle, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export const NotFoundPage: React.FC = () => {
  return (
    <div className="container flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4">
      <div className="rounded-full bg-emerald-100 p-4 text-emerald-700">
        <AlertCircle className="h-10 w-10" />
      </div>
      <h1 className="text-3xl font-bold tracking-tight">404 - Page Not Found</h1>
      <p className="text-muted-foreground max-w-md">
        The requested page does not exist or has been moved within NutriLens.
      </p>
      <Button asChild variant="default" className="mt-4">
        <Link to="/">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Overview
        </Link>
      </Button>
    </div>
  );
};
