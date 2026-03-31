"use client";

import { Plus, Cloud, Trash2 } from "lucide-react";
import { useRef, useEffect } from "react";

interface LibraryControlsProps {
  lists: string[];
  selectedList: string;
  onSelectList: (list: string) => void;
  isCreatingList: boolean;
  onStartCreateList: () => void;
  newListName: string;
  onNewListNameChange: (name: string) => void;
  onCreateList: () => void;
  onCancelCreate: () => void;
  sortBy: string;
  onSortChange: (sort: string) => void;
  onExport: () => void;
  isExporting: boolean;
  onDeleteList: () => void;
}

export default function LibraryControls({
  lists,
  selectedList,
  onSelectList,
  isCreatingList,
  onStartCreateList,
  newListName,
  onNewListNameChange,
  onCreateList,
  onCancelCreate,
  sortBy,
  onSortChange,
  onExport,
  isExporting,
  onDeleteList,
}: LibraryControlsProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isCreatingList && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isCreatingList]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      onCreateList();
    } else if (e.key === "Escape") {
      e.preventDefault();
      onCancelCreate();
    }
  };

  return (
    <section className="flex items-center justify-between gap-4 flex-wrap">
      {/* List pill tabs — horizontal scroll */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 flex-1">
        {/* "All" pill */}
        <button
          onClick={() => onSelectList("All")}
          className={`whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
            selectedList === "All"
              ? "bg-accent text-on-accent"
              : "bg-surface-inset text-foreground-muted hover:text-foreground-secondary"
          }`}
        >
          All
        </button>

        {/* Custom list pills */}
        {lists.map((list) => (
          <button
            key={list}
            onClick={() => onSelectList(list)}
            className={`whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
              selectedList === list
                ? "bg-accent text-on-accent"
                : "bg-surface-inset text-foreground-muted hover:text-foreground-secondary"
            }`}
          >
            {list}
          </button>
        ))}

        {/* "+ New List" pill or inline input */}
        {isCreatingList ? (
          <input
            ref={inputRef}
            type="text"
            value={newListName}
            onChange={(e) => onNewListNameChange(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={onCancelCreate}
            placeholder="List name..."
            className="bg-surface-inset rounded-full px-3 py-1.5 text-sm text-foreground placeholder:text-foreground-muted outline-none focus:ring-2 focus:ring-accent/20 min-w-[120px]"
          />
        ) : (
          <button
            onClick={onStartCreateList}
            className="flex items-center gap-1.5 whitespace-nowrap border-2 border-dashed border-accent/40 text-accent rounded-full px-4 py-1.5 text-sm hover:border-accent transition-colors"
          >
            <Plus size={14} />
            New List
          </button>
        )}
      </div>

      {/* Control bar — sort + actions */}
      <div className="flex items-center gap-3">
        {/* Sort dropdown */}
        <div className="flex items-center gap-2">
          <span className="text-foreground-muted text-sm">Sort by:</span>
          <select
            value={sortBy}
            onChange={(e) => onSortChange(e.target.value)}
            className="bg-surface-inset text-foreground-secondary rounded-full px-3 py-1.5 text-sm border-none outline-none cursor-pointer focus:ring-2 focus:ring-accent/20 appearance-auto"
          >
            <option value="date_added">Date Added</option>
            <option value="published_newest">Published (Newest)</option>
            <option value="published_oldest">Published (Oldest)</option>
            <option value="title_az">Title (A-Z)</option>
            <option value="title_za">Title (Z-A)</option>
          </select>
        </div>

        {/* Sync to Drive — only for specific lists */}
        {selectedList !== "All" && (
          <button
            onClick={onExport}
            disabled={isExporting}
            className="flex items-center gap-1.5 bg-surface-card text-foreground-secondary rounded-full px-4 py-1.5 text-sm shadow-warm-sm hover:text-foreground transition-colors disabled:opacity-50"
          >
            <Cloud size={14} />
            {isExporting ? "Syncing..." : "Sync to Drive"}
          </button>
        )}

        {/* Delete list — only for specific lists */}
        {selectedList !== "All" && (
          <button
            onClick={onDeleteList}
            className="text-foreground-muted hover:text-red-600 transition-colors p-1.5"
            title="Delete list"
          >
            <Trash2 size={16} />
          </button>
        )}
      </div>
    </section>
  );
}
