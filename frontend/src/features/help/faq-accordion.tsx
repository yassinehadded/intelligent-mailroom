import { ChevronDown, HelpCircle, ThumbsDown, ThumbsUp } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";

interface FaqItem {
  id: string;
  category: string;
  question: string;
  answer: string;
}

interface FaqAccordionProps {
  categoryFilter: string;
  searchQuery: string;
}

export function FaqAccordion({ categoryFilter, searchQuery }: FaqAccordionProps) {
  const { t } = useTranslation("help");
  const [openIds, setOpenIds] = useState<string[]>(["faq-1"]);
  const [feedbackState, setFeedbackState] = useState<Record<string, "up" | "down">>({});

  const faqItems = t("faq.items", { returnObjects: true }) as FaqItem[];

  const filteredFaqs = (faqItems || []).filter((item) => {
    const matchesCategory =
      categoryFilter === "all" || item.category === categoryFilter;
    const matchesSearch =
      !searchQuery.trim() ||
      item.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.answer.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const toggleItem = (id: string) => {
    setOpenIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    );
  };

  const handleFeedback = (id: string, type: "up" | "down", e: React.MouseEvent) => {
    e.stopPropagation();
    setFeedbackState((prev) => ({ ...prev, [id]: type }));
    toast.success(type === "up" ? "Thanks for your feedback!" : "Feedback recorded. We'll improve this answer.");
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold tracking-tight">{t("faq.title")}</h2>
        <p className="text-sm text-muted-foreground">{t("faq.subtitle")}</p>
      </div>

      {filteredFaqs.length === 0 ? (
        <Card className="flex flex-col items-center justify-center p-8 text-center border-dashed">
          <HelpCircle className="h-10 w-10 text-muted-foreground/50 mb-3" />
          <h3 className="text-sm font-semibold">No questions found</h3>
          <p className="text-xs text-muted-foreground mt-1">
            Try adjusting your search query or selecting another category.
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredFaqs.map((faq) => {
            const isOpen = openIds.includes(faq.id);
            const feedback = feedbackState[faq.id];

            return (
              <Card
                key={faq.id}
                className={`overflow-hidden border-border transition-all ${isOpen ? "ring-1 ring-primary/30 shadow-sm" : "hover:border-primary/40"
                  }`}
              >
                <button
                  type="button"
                  onClick={() => toggleItem(faq.id)}
                  className="flex w-full items-center justify-between gap-4 p-5 text-left transition-colors hover:bg-accent/40"
                >
                  <span className="text-sm font-semibold text-foreground">
                    {faq.question}
                  </span>
                  <ChevronDown
                    className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200 ${isOpen ? "rotate-180 text-primary" : ""
                      }`}
                  />
                </button>

                {isOpen && (
                  <div className="border-t border-border/60 bg-muted/20 px-5 py-4 text-xs text-muted-foreground leading-relaxed animate-in fade-in duration-150">
                    <p className="text-sm text-muted-foreground">{faq.answer}</p>

                    <div className="mt-4 flex items-center justify-between border-t border-border/40 pt-3 text-xs">
                      <span>Was this answer helpful?</span>
                      <div className="flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={(e) => handleFeedback(faq.id, "up", e)}
                          className={`flex items-center gap-1 rounded-md px-2 py-1 transition-colors ${feedback === "up"
                              ? "bg-emerald-500/10 text-emerald-600 font-semibold"
                              : "hover:bg-accent text-muted-foreground"
                            }`}
                        >
                          <ThumbsUp className="h-3.5 w-3.5" />
                          <span>Yes</span>
                        </button>
                        <button
                          type="button"
                          onClick={(e) => handleFeedback(faq.id, "down", e)}
                          className={`flex items-center gap-1 rounded-md px-2 py-1 transition-colors ${feedback === "down"
                              ? "bg-rose-500/10 text-rose-600 font-semibold"
                              : "hover:bg-accent text-muted-foreground"
                            }`}
                        >
                          <ThumbsDown className="h-3.5 w-3.5" />
                          <span>No</span>
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
