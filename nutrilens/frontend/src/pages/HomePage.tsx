import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ShieldAlert,
  Cpu,
  Database,
  Layers,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Award,
} from "lucide-react";
import { apiService } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

export const HomePage: React.FC = () => {
  const {
    data: health,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ["healthCheck"],
    queryFn: apiService.checkHealth,
    retry: 1,
    refetchInterval: 30000,
  });

  return (
    <div className="container py-10 space-y-12">
      {/* Hero Section */}
      <section className="text-center max-w-3xl mx-auto space-y-4">
        <Badge variant="subtle" className="text-emerald-700 bg-emerald-100 border-emerald-300 px-3 py-1 text-xs">
          Final-Year B.Tech Major Project • Day 1 Foundation
        </Badge>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-foreground leading-tight">
          Personalized Food Intelligence & <span className="text-emerald-600">Nutrition Decision</span> Platform
        </h1>
        <p className="text-muted-foreground text-lg sm:text-xl font-normal leading-relaxed">
          Decipher packaged food labels with explainable backend intelligence, deterministic allergen alerts, 
          and personalized dietary suitability.
        </p>
      </section>

      {/* System Status / Health Check Card */}
      <section id="status" className="max-w-2xl mx-auto">
        <Card className="border-emerald-100 shadow-md overflow-hidden">
          <div className="bg-gradient-to-r from-emerald-500 to-teal-600 px-6 py-4 text-white flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Cpu className="h-5 w-5" />
              <span className="font-semibold text-base">Backend Health Monitor</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isFetching}
              className="bg-white/10 hover:bg-white/20 text-white border-white/20 text-xs h-8"
            >
              <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${isFetching ? "animate-spin" : ""}`} />
              Refresh Check
            </Button>
          </div>
          <CardContent className="pt-6">
            {isLoading ? (
              <div className="flex items-center justify-center py-6 space-x-3 text-muted-foreground">
                <RefreshCw className="h-5 w-5 animate-spin text-emerald-600" />
                <span className="text-sm font-medium">Querying GET /api/health...</span>
              </div>
            ) : isError ? (
              <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-900 flex items-start space-x-3">
                <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
                <div className="text-sm space-y-1">
                  <p className="font-semibold">Backend Unreachable</p>
                  <p className="text-xs text-red-700">
                    {error instanceof Error ? error.message : "Failed to connect to FastAPI service at http://localhost:8000"}
                  </p>
                  <p className="text-xs text-red-600 mt-2">
                    Ensure the FastAPI server is running with <code className="bg-red-100 px-1 py-0.5 rounded font-mono">uvicorn app.main:app --reload</code>
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b">
                  <span className="text-sm text-muted-foreground">Service Status</span>
                  <Badge variant="excellent" className="flex items-center gap-1 font-semibold">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                    {health?.status.toUpperCase()}
                  </Badge>
                </div>
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="text-muted-foreground block mb-0.5">Application</span>
                    <span className="font-semibold text-foreground font-mono">{health?.app}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block mb-0.5">Version</span>
                    <span className="font-semibold text-foreground font-mono">v{health?.version}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block mb-0.5">Environment</span>
                    <span className="font-semibold text-foreground capitalize">{health?.environment}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block mb-0.5">Database Engine</span>
                    <span className="font-semibold text-foreground capitalize">{health?.database}</span>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </section>

      {/* Day 1 Foundation Architecture Section */}
      <section id="architecture" className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold tracking-tight">Platform Foundation & Engine Scaffolding</h2>
          <p className="text-sm text-muted-foreground">
            Architectural separation established on Day 1 according to the design specification.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader className="pb-3">
              <div className="h-8 w-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center mb-2">
                <Layers className="h-4 w-4" />
              </div>
              <CardTitle className="text-lg">Frontend Architecture</CardTitle>
              <CardDescription className="text-xs">
                React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui
              </CardDescription>
            </CardHeader>
            <CardContent className="text-xs space-y-2 text-muted-foreground">
              <div className="flex items-center gap-2 text-foreground font-medium">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                <span>Components, Layouts, Hooks, Services</span>
              </div>
              <div className="flex items-center gap-2 text-foreground font-medium">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                <span>TanStack Query & Axios API Client</span>
              </div>
              <div className="flex items-center gap-2 text-foreground font-medium">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                <span>React Hook Form, Zod & Recharts</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <div className="h-8 w-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center mb-2">
                <Cpu className="h-4 w-4" />
              </div>
              <CardTitle className="text-lg">Backend API & Engines</CardTitle>
              <CardDescription className="text-xs">
                FastAPI, SQLAlchemy, Pydantic, Alembic
              </CardDescription>
            </CardHeader>
            <CardContent className="text-xs space-y-2 text-muted-foreground">
              <div className="flex items-center gap-2 text-foreground font-medium">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                <span>app/food_scanner & app/ingredient_engine</span>
              </div>
              <div className="flex items-center gap-2 text-foreground font-medium">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                <span>app/scoring_engine & app/suitability_engine</span>
              </div>
              <div className="flex items-center gap-2 text-foreground font-medium">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                <span>app/recommendation_engine & tests</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <div className="h-8 w-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center mb-2">
                <Database className="h-4 w-4" />
              </div>
              <CardTitle className="text-lg">Database & Storage</CardTitle>
              <CardDescription className="text-xs">
                PostgreSQL (Supabase compatible) + Docker
              </CardDescription>
            </CardHeader>
            <CardContent className="text-xs space-y-2 text-muted-foreground">
              <div className="flex items-center gap-2 text-foreground font-medium">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                <span>Async SQLAlchemy Connection Layer</span>
              </div>
              <div className="flex items-center gap-2 text-foreground font-medium">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                <span>Alembic Migration System Ready</span>
              </div>
              <div className="flex items-center gap-2 text-foreground font-medium">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                <span>Local Docker Compose postgres Service</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Design System & Reusable UI Showcase */}
      <section className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold tracking-tight">Design System & Reusable Components</h2>
          <p className="text-sm text-muted-foreground">
            A cohesive, accessible UI system aligned with NutriLens brand identity.
          </p>
        </div>

        <Card>
          <CardContent className="pt-6">
            <Tabs defaultValue="buttons" className="w-full">
              <TabsList className="grid w-full grid-cols-3 max-w-md mx-auto mb-6">
                <TabsTrigger value="buttons">Buttons</TabsTrigger>
                <TabsTrigger value="badges">Nutritional Badges</TabsTrigger>
                <TabsTrigger value="principles">Core Rules</TabsTrigger>
              </TabsList>

              <TabsContent value="buttons" className="space-y-4">
                <div className="flex flex-wrap items-center justify-center gap-3">
                  <Button variant="default">Primary Action</Button>
                  <Button variant="secondary">Secondary Action</Button>
                  <Button variant="outline">Outline Action</Button>
                  <Button variant="subtle">Subtle Emerald</Button>
                  <Button variant="destructive">Destructive Action</Button>
                </div>
              </TabsContent>

              <TabsContent value="badges" className="space-y-4">
                <div className="flex flex-wrap items-center justify-center gap-3">
                  <Badge variant="excellent">NutriScore: Excellent (A)</Badge>
                  <Badge variant="moderate">NutriScore: Moderate (C)</Badge>
                  <Badge variant="alert">Allergen Alert: Peanut Declared</Badge>
                  <Badge variant="secondary">Precautionary: May Contain Soy</Badge>
                  <Badge variant="outline">Uncertain OCR Quality</Badge>
                </div>
              </TabsContent>

              <TabsContent value="principles" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="flex items-start gap-2 p-3 rounded-lg border bg-muted/20">
                    <Award className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-semibold text-foreground">Traceable & Deterministic</p>
                      <p className="text-muted-foreground">Every score is computed via explainable backend rules, never invented by an LLM.</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-2 p-3 rounded-lg border bg-muted/20">
                    <ShieldAlert className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-semibold text-foreground">Explicit Consent & Logging</p>
                      <p className="text-muted-foreground">Products scanned never automatically enter the journal without explicit user confirmation.</p>
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </section>
    </div>
  );
};
