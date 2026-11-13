import React from "react";
import { Award, Plus, ShoppingBag } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { FrequentProductItem } from "@/types";

interface FrequentProductsCardProps {
  products: FrequentProductItem[];
  onLogAgain: (prod: { id: string; name: string; brand?: string | null; serving_size?: string | null }) => void;
}

export const FrequentProductsCard: React.FC<FrequentProductsCardProps> = ({
  products,
  onLogAgain,
}) => {
  if (products.length === 0) {
    return (
      <Card className="border-slate-200 shadow-xs text-center p-6">
        <CardContent className="space-y-2 max-w-sm mx-auto">
          <div className="h-10 w-10 rounded-xl bg-slate-100 text-slate-500 flex items-center justify-center mx-auto">
            <ShoppingBag className="h-5 w-5" />
          </div>
          <h4 className="text-sm font-bold text-slate-800">No Frequent Foods Yet</h4>
          <p className="text-xs text-slate-500">
            As you log meals, your most commonly consumed packaged items will appear here for fast re-logging.
          </p>
        </CardContent>
      </Card>
    );
  }

  const formatLastConsumed = (isoStr: string) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
    } catch {
      return isoStr.slice(0, 10);
    }
  };

  return (
    <Card className="border-slate-200 shadow-xs">
      <CardContent className="p-5 sm:p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 bg-amber-100 text-amber-800 rounded-lg">
              <Award className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Frequently Logged Products</h3>
              <p className="text-xs text-slate-500">Your most commonly consumed packaged foods</p>
            </div>
          </div>
          <Badge variant="outline" className="text-xs bg-slate-50">
            Top {products.length}
          </Badge>
        </div>

        <div className="divide-y divide-slate-100">
          {products.map((item, index) => (
            <div
              key={item.product_id}
              className="py-3 first:pt-0 last:pb-0 flex items-center justify-between gap-3"
            >
              <div className="flex items-center space-x-3 min-w-0">
                <span className={`w-5 text-center font-bold text-xs shrink-0 ${
                  index === 0 ? "text-amber-600 font-extrabold" : index === 1 ? "text-slate-500 font-bold" : "text-slate-400"
                }`}>
                  #{index + 1}
                </span>

                {item.product_image_url ? (
                  <img
                    src={item.product_image_url}
                    alt={item.product_name}
                    className="h-10 w-10 rounded-lg object-cover border border-slate-200 shrink-0 bg-white"
                  />
                ) : (
                  <div className="h-10 w-10 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold text-xs shrink-0">
                    {item.product_name.slice(0, 2).toUpperCase()}
                  </div>
                )}

                <div className="min-w-0">
                  <div className="font-semibold text-sm text-slate-900 truncate">
                    {item.product_name}
                  </div>
                  <div className="text-xs text-slate-500 flex items-center gap-2 mt-0.5">
                    {item.product_brand && <span>{item.product_brand}</span>}
                    <span>• {item.log_count} {item.log_count === 1 ? "time" : "times"} ({item.total_weight_g}g total)</span>
                    <span className="hidden sm:inline text-slate-400">
                      • Last: {formatLastConsumed(item.last_consumed_at)}
                    </span>
                  </div>
                </div>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  onLogAgain({
                    id: item.product_id,
                    name: item.product_name,
                    brand: item.product_brand,
                  })
                }
                className="h-8 text-xs text-slate-700 hover:text-emerald-700 hover:bg-emerald-50 shrink-0"
              >
                <Plus className="h-3 w-3 mr-1" />
                Log Again
              </Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
