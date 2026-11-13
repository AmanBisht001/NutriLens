import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Search,
  Filter,
  X,
  BookOpen,
  Loader2,
  AlertCircle,
  PackageSearch,
  Info,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { apiService } from "@/services/api";
import type { ProductSummary, CategoryItem } from "@/types";
import { ProductCard } from "@/components/catalogue/ProductCard";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export const FoodCataloguePage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filter and pagination state
  const [searchInput, setSearchInput] = useState<string>(searchParams.get("search") || "");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(
    searchParams.get("category") || null
  );
  const [currentPage, setCurrentPage] = useState<number>(
    parseInt(searchParams.get("page") || "1", 10)
  );
  const [totalPages, setTotalPages] = useState<number>(1);
  const [totalItems, setTotalItems] = useState<number>(0);

  // Fetch categories on mount
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const data = await apiService.getCategories();
        setCategories(data.categories);
      } catch (err) {
        console.error("Failed to load product categories:", err);
      }
    };
    fetchCategories();
  }, []);

  // Fetch products when query params change
  useEffect(() => {
    const fetchProducts = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiService.getProducts({
          search: searchInput || undefined,
          category: selectedCategory || undefined,
          page: currentPage,
          page_size: 9,
        });
        setProducts(data.items);
        setTotalPages(data.total_pages);
        setTotalItems(data.total);
      } catch (err: any) {
        setError(err.response?.data?.detail || "Failed to load products from catalogue.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchProducts();
  }, [searchInput, selectedCategory, currentPage]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (searchInput) next.set("search", searchInput);
      else next.delete("search");
      next.set("page", "1");
      return next;
    });
  };

  const handleClearSearch = () => {
    setSearchInput("");
    setCurrentPage(1);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.delete("search");
      next.set("page", "1");
      return next;
    });
  };

  const handleCategorySelect = (catName: string | null) => {
    setSelectedCategory(catName);
    setCurrentPage(1);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (catName) next.set("category", catName);
      else next.delete("category");
      next.set("page", "1");
      return next;
    });
  };

  const resetAllFilters = () => {
    setSearchInput("");
    setSelectedCategory(null);
    setCurrentPage(1);
    setSearchParams(new URLSearchParams());
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-emerald-700 font-semibold text-xs tracking-wider uppercase mb-1">
            <BookOpen className="h-4 w-4" />
            <span>Product Catalogue & Ingredient Repository</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
            Food Catalogue
          </h1>
          <p className="text-sm text-slate-600 mt-1 max-w-2xl leading-relaxed">
            Search packaged groceries, inspect full nutritional facts, and explore structured
            knowledge-base breakdowns of preservatives, emulsifiers, sweeteners, and allergens.
          </p>
        </div>

        {/* Demo dataset disclaimer badge */}
        <div className="flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 max-w-sm">
          <Info className="h-4 w-4 text-amber-600 flex-shrink-0" />
          <span>
            <strong className="font-semibold">Demonstration Data:</strong> Development dataset with
            illustrative values. Keep distinguishable from verified records.
          </span>
        </div>
      </div>

      {/* Search Bar & Category Filter Controls */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        {/* Search input form */}
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              type="text"
              placeholder="Search by product name or brand (e.g. NutriDemo, Cola, Biscuits)..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="pl-10 pr-9 border-slate-200 focus-visible:ring-emerald-500"
            />
            {searchInput && (
              <button
                type="button"
                onClick={handleClearSearch}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                aria-label="Clear search"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
          <Button type="submit" className="bg-emerald-600 hover:bg-emerald-700 text-white px-5">
            Search
          </Button>
        </form>

        {/* Category Filter Pills */}
        <div className="space-y-1.5 pt-1">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500 uppercase tracking-wider">
            <span className="flex items-center gap-1.5">
              <Filter className="h-3.5 w-3.5" /> Filter by Category
            </span>
            {(selectedCategory || searchInput) && (
              <button
                type="button"
                onClick={resetAllFilters}
                className="text-emerald-700 hover:text-emerald-800 font-semibold normal-case underline"
              >
                Reset filters
              </button>
            )}
          </div>

          <div className="flex flex-wrap gap-2 pt-1">
            {/* All Categories Pill */}
            <button
              type="button"
              onClick={() => handleCategorySelect(null)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                selectedCategory === null
                  ? "bg-emerald-600 text-white border-emerald-600 shadow-xs"
                  : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
              }`}
            >
              All Categories ({categories.reduce((acc, c) => acc + c.product_count, 0)})
            </button>

            {/* Individual Category Pills */}
            {categories.map((cat) => {
              const isSelected = selectedCategory === cat.name;
              return (
                <button
                  key={cat.name}
                  type="button"
                  onClick={() => handleCategorySelect(cat.name)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors flex items-center gap-1.5 ${
                    isSelected
                      ? "bg-emerald-600 text-white border-emerald-600 shadow-xs"
                      : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  <span>{cat.name}</span>
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
                      isSelected ? "bg-emerald-700 text-white" : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {cat.product_count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Results Section */}
      {isLoading ? (
        <div className="py-20 flex flex-col items-center justify-center space-y-3">
          <Loader2 className="h-8 w-8 text-emerald-600 animate-spin" />
          <p className="text-sm text-slate-500 font-medium">Loading product catalogue...</p>
        </div>
      ) : error ? (
        <div className="p-6 rounded-2xl bg-red-50 border border-red-200 text-center space-y-3 max-w-lg mx-auto">
          <AlertCircle className="h-8 w-8 text-red-600 mx-auto" />
          <h3 className="font-bold text-red-900 text-base">Error Loading Catalogue</h3>
          <p className="text-xs text-red-700">{error}</p>
          <Button onClick={resetAllFilters} variant="outline" size="sm">
            Retry
          </Button>
        </div>
      ) : products.length === 0 ? (
        /* Empty State */
        <div className="p-12 bg-white rounded-2xl border border-slate-200 text-center space-y-4 shadow-sm">
          <div className="h-16 w-16 mx-auto rounded-2xl bg-slate-100 text-slate-500 flex items-center justify-center">
            <PackageSearch className="h-8 w-8" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">No matching products found</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto leading-relaxed">
            {searchInput
              ? `No food products matched your query "${searchInput}". Try adjusting keywords or clearing category filters.`
              : "There are no products currently available in this category."}
          </p>
          <Button onClick={resetAllFilters} className="bg-emerald-600 hover:bg-emerald-700 text-white">
            Reset Search & Filters
          </Button>
        </div>
      ) : (
        /* Product Cards Grid */
        <div className="space-y-6">
          <div className="flex items-center justify-between text-xs text-slate-500 px-1">
            <span>
              Showing <strong className="text-slate-800">{products.length}</strong> of{" "}
              <strong className="text-slate-800">{totalItems}</strong> products
              {selectedCategory && ` in "${selectedCategory}"`}
            </span>
            <span>
              Page {currentPage} of {totalPages}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center space-x-2 pt-4">
              <Button
                variant="outline"
                size="sm"
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                className="flex items-center gap-1"
              >
                <ChevronLeft className="h-4 w-4" /> Previous
              </Button>

              <div className="flex items-center space-x-1 px-2">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
                  <button
                    key={pageNum}
                    type="button"
                    onClick={() => setCurrentPage(pageNum)}
                    className={`h-8 w-8 rounded-lg text-xs font-semibold transition-colors ${
                      currentPage === pageNum
                        ? "bg-emerald-600 text-white shadow-xs"
                        : "text-slate-700 hover:bg-slate-100"
                    }`}
                  >
                    {pageNum}
                  </button>
                ))}
              </div>

              <Button
                variant="outline"
                size="sm"
                disabled={currentPage >= totalPages}
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                className="flex items-center gap-1"
              >
                Next <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
