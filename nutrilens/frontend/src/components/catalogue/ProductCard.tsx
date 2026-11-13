import React from "react";
import { Link } from "react-router-dom";
import {
  ShieldCheck,
  ChevronRight,
  Scale,
  ArrowLeftRight,
  BookMarked,
} from "lucide-react";
import type { ProductSummary } from "@/types";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface ProductCardProps {
  product: ProductSummary;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product }) => {
  const nf = product.nutrition_facts;

  return (
    <Card className="flex flex-col justify-between border-slate-200 hover:border-emerald-300 hover:shadow-md transition-all duration-200 bg-white group">
      <div>
        <CardHeader className="p-5 pb-3 space-y-2">
          {/* Top badges row */}
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="flex items-center gap-1.5 flex-wrap">
              {product.category && (
                <Badge
                  variant="outline"
                  className="text-xs bg-slate-50 text-slate-700 border-slate-200 font-medium"
                >
                  {product.category}
                </Badge>
              )}
              {product.is_demo_data && (
                <Badge
                  variant="outline"
                  className="text-[10px] bg-amber-50 text-amber-800 border-amber-200 font-semibold"
                >
                  Demo Data
                </Badge>
              )}
            </div>

            {product.is_verified ? (
              <Badge className="bg-emerald-100 text-emerald-800 border-emerald-300 text-[10px] flex items-center gap-1">
                <ShieldCheck className="h-3 w-3" /> Verified
              </Badge>
            ) : (
              <Badge variant="secondary" className="text-[10px] text-slate-500 bg-slate-100">
                Unverified
              </Badge>
            )}
          </div>

          {/* Product Name & Brand */}
          <div className="pt-1">
            <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">
              {product.brand || "Generic Brand"}
            </p>
            <h3 className="text-base font-bold text-slate-900 group-hover:text-emerald-700 transition-colors line-clamp-2">
              {product.name}
            </h3>
          </div>
        </CardHeader>

        <CardContent className="px-5 py-2 space-y-3">
          {/* Serving size and barcode */}
          <div className="flex items-center justify-between text-xs text-slate-500 border-t border-slate-100 pt-2">
            {product.serving_size && (
              <span className="flex items-center gap-1">
                <Scale className="h-3.5 w-3.5 text-slate-400" />
                Serving: {product.serving_size}
              </span>
            )}
            {product.barcode && (
              <span className="font-mono text-[11px] text-slate-400">
                #{product.barcode}
              </span>
            )}
          </div>

          {/* Key nutritional facts snapshot */}
          {nf ? (
            <div className="grid grid-cols-4 gap-1.5 p-2.5 rounded-lg bg-slate-50/80 border border-slate-100 text-center">
              <div className="flex flex-col">
                <span className="text-[10px] text-slate-500 font-medium">Energy</span>
                <span className="text-xs font-bold text-slate-800">
                  {nf.energy_kcal !== null && nf.energy_kcal !== undefined
                    ? `${nf.energy_kcal} kcal`
                    : "—"}
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] text-slate-500 font-medium">Protein</span>
                <span className="text-xs font-bold text-slate-800">
                  {nf.protein_g !== null && nf.protein_g !== undefined ? `${nf.protein_g}g` : "—"}
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] text-slate-500 font-medium">Carbs</span>
                <span className="text-xs font-bold text-slate-800">
                  {nf.carbohydrates_g !== null && nf.carbohydrates_g !== undefined
                    ? `${nf.carbohydrates_g}g`
                    : "—"}
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] text-slate-500 font-medium">Fat</span>
                <span className="text-xs font-bold text-slate-800">
                  {nf.total_fat_g !== null && nf.total_fat_g !== undefined
                    ? `${nf.total_fat_g}g`
                    : "—"}
                </span>
              </div>
            </div>
          ) : (
            <div className="p-2.5 text-center text-xs text-slate-400 bg-slate-50 rounded-lg">
              Nutrition values pending verification
            </div>
          )}
        </CardContent>
      </div>

      <CardFooter className="p-4 pt-3 border-t border-slate-100 bg-slate-50/40 flex items-center gap-2">
        <Button
          asChild
          variant="outline"
          size="sm"
          className="flex-1 justify-between hover:bg-emerald-600 hover:text-white hover:border-emerald-600 transition-colors text-xs"
        >
          <Link to={`/catalogue/${product.id}`}>
            <span>View Details</span>
            <ChevronRight className="h-4 w-4" />
          </Link>
        </Button>
        <Button
          asChild
          variant="ghost"
          size="sm"
          className="text-xs text-slate-600 hover:text-emerald-700 hover:bg-emerald-50 px-2 h-8 font-medium"
          title="Log in Food Journal"
        >
          <Link to="/journal" state={{ logProduct: product }}>
            <BookMarked className="h-3.5 w-3.5" />
          </Link>
        </Button>
        <Button
          asChild
          variant="ghost"
          size="sm"
          className="text-xs text-slate-600 hover:text-emerald-700 hover:bg-emerald-50 px-2.5 h-8 font-medium"
          title="Compare with other products"
        >
          <Link to={`/compare?products=${product.id}`}>
            <ArrowLeftRight className="h-3.5 w-3.5 mr-1" /> Compare
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
};
