import { useState, useCallback } from "react";
import { useDispatch } from "react-redux";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { clearPresentationData } from "@/store/slices/presentationGeneration";
import { PresentationGenerationApi } from "../../services/api/presentation-generation";
import { LayoutGroup, LoadingState, TABS } from "../types/index";
import { MixpanelEvent, trackEvent } from "@/utils/mixpanel";

const DEFAULT_LOADING_STATE: LoadingState = {
  message: "",
  isLoading: false,
  showProgress: false,
  duration: 0,
};

export const usePresentationGeneration = (
  presentationId: string | null,
  outlines: { content: string }[] | null,
  selectedLayoutGroup: LayoutGroup | null,
  setActiveTab: (tab: string) => void
) => {
  const dispatch = useDispatch();
  const router = useRouter();
  const [loadingState, setLoadingState] = useState<LoadingState>(DEFAULT_LOADING_STATE);

  const validateInputs = useCallback(() => {
    console.log("🔍 Validando inputs para generación:", {
      presentation_id: presentationId,
      outlines: outlines ? {
        count: outlines.length,
        firstSlide: outlines[0]?.content?.substring(0, 50) + "..." || "No content"
      } : "No outlines",
      selectedLayoutGroup: selectedLayoutGroup ? {
        id: selectedLayoutGroup.id,
        name: selectedLayoutGroup.name,
        hasSlides: !!selectedLayoutGroup.slides,
        slidesLength: selectedLayoutGroup.slides?.length || 0
      } : null
    });

    if (!outlines || outlines.length === 0) {
      toast.error("No Outlines", {
        description: "Please wait for outlines to load before generating presentation",
      });
      return false;
    }

    if (!selectedLayoutGroup) {
      toast.error("Select Layout Group", {
        description: "Please select a layout group before generating presentation",
      });
      return false;
    }
    if (!selectedLayoutGroup.slides || !selectedLayoutGroup.slides.length) {
      toast.error("No Slide Schema found", {
        description: "Please select a Group before generating presentation",
      });
      return false;
    }

    return true;
  }, [outlines, selectedLayoutGroup]);

  const prepareLayoutData = useCallback(() => {
    if (!selectedLayoutGroup) return null;

    console.log("Preparando layout data:", {
      name: selectedLayoutGroup.name,
      ordered: selectedLayoutGroup.ordered,
      slides: selectedLayoutGroup.slides ? selectedLayoutGroup.slides.length : 0
    });

    // Usar el layout original, el backend se encargará de detectar y generar preguntas
    return {
      name: selectedLayoutGroup.name,
      ordered: selectedLayoutGroup.ordered,
      slides: selectedLayoutGroup.slides
    };
  }, [selectedLayoutGroup]);

  const handleSubmit = useCallback(async () => {
    if (!selectedLayoutGroup) {
      setActiveTab(TABS.LAYOUTS);
      return;
    }
    
    // Si no hay presentation_id válido (es temporal), crear uno nuevo
    if (!presentationId || presentationId.startsWith('theme-')) {
      console.log("⚠️ presentation_id temporal detectado, creando presentación temporal");
      
      try {
        // Crear una presentación temporal para este tema
        const tempPresentationResponse = await fetch('/api/v1/ppt/presentation/create-from-theme', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            outlines: outlines || [],
            title: outlines?.[0]?.content?.substring(0, 50) || "Presentación desde tema",
            language: "es",
            n_slides: outlines?.length || 0
          }),
        });
        
        if (!tempPresentationResponse.ok) {
          throw new Error('Failed to create temporary presentation');
        }
        
        const tempPresentation = await tempPresentationResponse.json();
        
        // Usar el nuevo presentation_id para continuar
        console.log("✅ Presentación temporal creada:", tempPresentation.id);
        
        // Continuar con el flujo normal usando el nuevo ID
        const layoutData = prepareLayoutData();
        if (!layoutData) return;
        
        const response = await PresentationGenerationApi.presentationPrepare({
          presentation_id: tempPresentation.id,
          outlines: outlines,
          layout: layoutData,
        });

        if (response) {
          dispatch(clearPresentationData());
          router.replace(`/presentation?id=${tempPresentation.id}&stream=true`);
        }
        return;
        
      } catch (error) {
        console.error("Error creando presentación temporal:", error);
        toast.error("Error creando presentación desde tema. Ve al tab 'Outline & Content' y genera outlines nuevos.");
        setActiveTab(TABS.OUTLINE);
        return;
      }
    }
    
    if (!validateInputs()) return;



    setLoadingState({
      message: "Generating presentation data...",
      isLoading: true,
      showProgress: true,
      duration: 30,
    });

    try {
      const layoutData = prepareLayoutData();

      if (!layoutData) return;

      // Agregar automáticamente un slide de preguntas al final
      let modifiedOutlines = outlines ? [...outlines] : [];

      if (modifiedOutlines.length > 0) {
        // Crear un nuevo outline para preguntas que será generado con IA
        const questionsOutline = {
          content: `🎯 Evaluación de Conocimientos

Esta evaluación contiene preguntas interactivas basadas en el contenido completo de la presentación. Las preguntas serán generadas automáticamente usando inteligencia artificial para evaluar la comprensión del material presentado.`
        };

        modifiedOutlines.push(questionsOutline);
      }

      console.log("📤 Datos finales enviados al API:", {
        presentation_id: presentationId,
        outlines: {
          count: modifiedOutlines.length,
          preview: modifiedOutlines.slice(0, 2).map(o => ({
            content: o.content?.substring(0, 100) + "..."
          })) || []
        },
        layout: {
          name: layoutData.name,
          ordered: layoutData.ordered,
          slidesCount: layoutData.slides?.length || 0
        }
      });

      trackEvent(MixpanelEvent.Presentation_Prepare_API_Call);
      const response = await PresentationGenerationApi.presentationPrepare({
        presentation_id: presentationId,
        outlines: modifiedOutlines,
        layout: layoutData,
      });

      if (response) {
        dispatch(clearPresentationData());
        router.replace(`/presentation?id=${presentationId}&stream=true`);
      }
    } catch (error: any) {
      console.error('Error In Presentation Generation(prepare).', error);
      toast.error("Generation Error", {
        description: error.message || "Error In Presentation Generation(prepare).",
      });
    } finally {
      setLoadingState(DEFAULT_LOADING_STATE);
    }
  }, [validateInputs, prepareLayoutData, presentationId, outlines, dispatch, router]);

  return { loadingState, handleSubmit };
}; 