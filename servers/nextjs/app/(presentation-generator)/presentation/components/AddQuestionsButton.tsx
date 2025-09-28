"use client";
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { HelpCircle, Loader2, Plus } from "lucide-react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { trackEvent, MixpanelEvent } from "@/utils/mixpanel";

interface AddQuestionsButtonProps {
  presentation_id: string;
  disabled?: boolean;
}

const AddQuestionsButton: React.FC<AddQuestionsButtonProps> = ({
  presentation_id,
  disabled = false,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [hasQuestions, setHasQuestions] = useState<boolean | null>(null);
  const router = useRouter();

  const checkQuestionsStatus = async () => {
    try {
      const response = await fetch('/api/v1/ppt/check-questions-slide', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(presentation_id),
      });

      if (response.ok) {
        const data = await response.json();
        setHasQuestions(data.has_questions_slide);
        return data;
      } else {
        throw new Error('Failed to check questions status');
      }
    } catch (error) {
      console.error('Error checking questions status:', error);
      return null;
    }
  };

  const addQuestionsSlide = async () => {
    if (disabled || isLoading) return;

    setIsLoading(true);
    
    try {
      // First check if questions already exist
      const status = await checkQuestionsStatus();
      
      if (status?.has_questions_slide) {
        toast.info("¡Preguntas ya disponibles!", {
          description: "Esta presentación ya tiene un slide de preguntas interactivas.",
        });
        setIsLoading(false);
        return;
      }

      if (!status?.can_add_questions) {
        toast.error("No se pueden agregar preguntas", {
          description: status?.message || "No es posible agregar preguntas a esta presentación.",
        });
        setIsLoading(false);
        return;
      }

      // Add questions slide
      const response = await fetch('/api/v1/ppt/add-questions-slide', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(presentation_id),
      });

      if (response.ok) {
        const data = await response.json();
        
        toast.success("¡Preguntas agregadas!", {
          description: "Se ha agregado un slide interactivo de preguntas al final de tu presentación.",
        });

        // Track the event
        trackEvent(MixpanelEvent.Presentation_Add_Questions_Slide);

        // Refresh the page to show the new slide
        router.refresh();
        
        setHasQuestions(true);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to add questions slide');
      }
    } catch (error: any) {
      console.error('Error adding questions slide:', error);
      
      let errorMessage = "No se pudieron agregar las preguntas.";
      let errorDescription = "Ocurrió un error inesperado. Por favor intenta de nuevo.";
      
      if (error.message.includes("already exists")) {
        errorMessage = "¡Preguntas ya disponibles!";
        errorDescription = "Esta presentación ya tiene un slide de preguntas.";
        setHasQuestions(true);
      } else if (error.message.includes("no slides")) {
        errorMessage = "Presentación vacía";
        errorDescription = "No se pueden agregar preguntas a una presentación sin slides.";
      }
      
      toast.error(errorMessage, {
        description: errorDescription,
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-check status on first render if not already checked
  React.useEffect(() => {
    if (hasQuestions === null && presentation_id) {
      checkQuestionsStatus();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [presentation_id]);

  if (hasQuestions === true) {
    // If questions already exist, show a different state
    return (
      <Button
        variant="ghost"
        className="border border-white/50 font-bold text-white/70 rounded-[32px] cursor-not-allowed"
        disabled
      >
        <HelpCircle className="w-4 h-4 mr-1" />
        Preguntas ✓
      </Button>
    );
  }

  return (
    <Button
      onClick={addQuestionsSlide}
      disabled={disabled || isLoading}
      variant="ghost"
      className="border border-white font-bold text-white rounded-[32px] transition-all duration-300 group hover:bg-white hover:text-[#5146E5] disabled:opacity-50"
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 mr-1 animate-spin" />
      ) : (
        <Plus className="w-4 h-4 mr-1 group-hover:text-[#5146E5]" />
      )}
      {isLoading ? "Agregando..." : "Agregar Preguntas"}
    </Button>
  );
};

export default AddQuestionsButton;
