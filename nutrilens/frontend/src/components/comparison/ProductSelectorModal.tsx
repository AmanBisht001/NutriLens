import React, { useState, useEffect } from "react";
import { Search, Plus, Check, X, Loader2 } from "lucide-react";
import { apiService } from "@/services/api";
import type { ProductSummary } from "@/types";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface ProductSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedProductIds: string[];
  onSelectProduct: (product: ProductSummary) => void;
}

export const ProductSelectorModal: React.FC<ProductSelectorModalProps> = ({
  isOpen,
  onClose,
  selectedProductIds,
  onSelectProduct,
}) => {
  const [search, setSearch] = useState("");
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) return;

    const fetchProducts = async () => {
      setIsLoading(true);
      try {
        const resp = await apiService.getProducts({
          search: search.trim() || undefined,
          page_size: 20,
        });
        setProducts(resp.items);
      } catch (err) {
        console.error("Failed to load products for selector:", err);
      } finally {
        setIsLoading(false);
      }
    };

    const timer = setTimeout(fetchProducts, 300);
    return () => clearTimeout(timer);
  }, [isOpen, search]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-in fade-in">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-lg w-full max-h-[85vh] flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="p-4 sm:p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-slate-900">Add Product to Compare</h3>
            <p className="text-xs text-slate-500">
              Select packaged food items from the verified catalogue
            </p>
          </div>
          <button
            onClick={onClose}
            className="h-8 w-8 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 flex items-center justify-center"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Search Input */}
        <div className="p-4 border-b border-slate-100 bg-slate-50/50">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              type="text"
              placeholder="Search products by brand or name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 bg-white"
              autoFocus
            />
          </div>
        </div>

        {/* Products List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {isLoading ? (
            <div className="py-12 flex flex-col items-center justify-center gap-2 text-slate-400">
              <Loader2 className="h-6 w-6 animate-spin text-emerald-600" />
              <span className="text-xs">Searching catalogue...</span>
            </div>
          ) : products.length === 0 ? (
            <div className="py-12 text-center text-slate-400 text-sm">
              No products found matching "{search}".
            </div>
          ) : (
            products.map((prod) => {
              const isAlreadySelected = selectedProductIds.includes(prod.id);

              return (
                <div
                  key={prod.id}
                  className={`p-3 rounded-xl border flex items-center justify-between gap-3 transition-colors ${
                    isAlreadySelected
                      ? "bg-emerald-50/50 border-emerald-200"
                      : "bg-white hover:bg-slate-50 border-slate-200"
                  }`}
                >
                  <div className="space-y-0.5 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-[10px] font-bold text-emerald-700 uppercase">
                        {prod.brand || "Brand"}
                      </span>
                      {prod.category && (
                        <Badge
                          variant="outline"
                          className="text-[10px] py-0 px-1.5 bg-slate-50 border-slate-200 text-slate-600"
                        >
                          {prod.category}
                        </Badge>
                      )}
                    </div>
                    <h4 className="text-sm font-semibold text-slate-900 truncate">
                      {prod.name}
                    </h4>
                    {prod.serving_size && (
                      <span className="text-[11px] text-slate-500">
                        Serving: {prod.serving_size}
                      </span>
                    )}
                  </div>

                  <div>
                    {isAlreadySelected ? (
                      <Badge className="bg-emerald-100 text-emerald-800 border-emerald-300 text-xs">
                        <Check className="h-3 w-3 mr-1" /> Added
                      </Badge>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          onSelectProduct(prod);
                          onClose();
                        }}
                        className="text-xs border-emerald-600 text-emerald-700 hover:bg-emerald-50"
                      >
                        <Plus className="h-3.5 w-3.5 mr-1" /> Add
                      </Button>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
