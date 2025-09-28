"use client";

import React, { useState, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RootState } from "@/store/store";
import { useSelector } from "react-redux";
import { OverlayLoader } from "@/components/ui/overlay-loader";
import Wrapper from "@/components/Wrapper";
import OutlineContent from "./OutlineContent";
import LayoutSelection from "./LayoutSelection";
import EmptyStateView from "./EmptyStateView";
import GenerateButton from "./GenerateButton";
import ThemesContent from "./ThemesContent";
import { useSearchParams } from "next/navigation";

import { TABS, LayoutGroup } from "../types/index";
import { useOutlineStreaming } from "../hooks/useOutlineStreaming";
import { useOutlineManagement } from "../hooks/useOutlineManagement";
import { usePresentationGeneration } from "../hooks/usePresentationGeneration";
import { useThemesStreaming } from "../hooks/useThemesStreaming";
import { selectTheme, setSavedThemes, saveThemeCollection, selectThemeInCollection, setPresentationId, cleanTestThemes } from "@/store/slices/presentationGeneration";
import { PresentationGenerationApi } from "../../services/api/presentation-generation";
import { useDispatch } from "react-redux";
import { toast } from "sonner";

const OutlinePage: React.FC = () => {
  const { presentation_id, outlines, themes, savedThemes, selectedThemeIndex, themeCollections, selectedCollectionId } = useSelector(
    (state: RootState) => state.presentationGeneration
  );
  const dispatch = useDispatch();
  const searchParams = useSearchParams();

  // Limpiar automáticamente temas de prueba al cargar la página (una sola vez)
  useEffect(() => {
    dispatch(cleanTestThemes());
  }, []); // Array vacío para que solo se ejecute una vez

  const [activeTab, setActiveTab] = useState<string>(TABS.OUTLINE);
  const [selectedLayoutGroup, setSelectedLayoutGroup] = useState<LayoutGroup | null>(null);

  // Debug: Log cuando cambia selectedLayoutGroup
  useEffect(() => {
    if (selectedLayoutGroup) {
      console.log("🎨 Plantilla seleccionada:", {
        id: selectedLayoutGroup.id,
        name: selectedLayoutGroup.name,
        hasSlides: !!selectedLayoutGroup.slides,
        slidesCount: selectedLayoutGroup.slides?.length || 0
      });
    } else {
      console.log("❌ No hay plantilla seleccionada");
    }
  }, [selectedLayoutGroup]);

  // Debug: Log cuando cambian los outlines
  useEffect(() => {
    if (outlines && outlines.length > 0) {
      console.log("📝 Outlines actualizados:", {
        count: outlines.length,
        selectedThemeIndex,
        firstSlidePreview: outlines[0]?.content?.substring(0, 100) + "..." || "No content"
      });
    }
  }, [outlines, selectedThemeIndex]);

  // Leer parámetro de tab de la URL al cargar el componente
  useEffect(() => {
    const tabParam = searchParams.get('tab');
    if (tabParam && Object.values(TABS).includes(tabParam as any)) {
      setActiveTab(tabParam);
    }
  }, [searchParams]);
  // Custom hooks
  const streamState = useOutlineStreaming(presentation_id);
  const { handleDragEnd, handleAddSlide } = useOutlineManagement(outlines);
  const { loadingState, handleSubmit } = usePresentationGeneration(
    presentation_id,
    outlines,
    selectedLayoutGroup,
    setActiveTab
  );
  const { startThemesGeneration, isStreaming: themesStreaming, isLoading: themesLoading } = useThemesStreaming(presentation_id);

  const handleGenerateThemes = () => {
    startThemesGeneration();
  };

  const handleSelectTheme = (themeIndex: number) => {
    // Usar la nueva acción selectTheme que maneja todo automáticamente
    dispatch(selectTheme({ themeIndex }));
    // Switch to outline tab to show the selected theme's content
    setActiveTab(TABS.OUTLINE);
  };

  const handleSaveThemesManually = (collectionName: string) => {
    if (themes && themes.length > 0) {
      // Guardar como colección de temas
      dispatch(saveThemeCollection({ name: collectionName, themes }));
      
      toast.success(`¡Colección guardada exitosamente!`, {
        description: `"${collectionName}" con ${themes.length} temas guardada.`
      });
    }
  };

  // Manejar selección de tema individual cuando hay una colección activa
  const handleSelectThemeInCurrentContext = (themeIndex: number) => {
    if (selectedCollectionId) {
      // Si hay una colección seleccionada, cambiar tema dentro de esa colección
      dispatch(selectThemeInCollection({ themeIndex }));
    } else {
      // Funcionalidad original para temas individuales
      dispatch(selectTheme({ themeIndex }));
    }
    setActiveTab(TABS.OUTLINE);
  };
  // Solo mostrar EmptyStateView si no hay presentation_id Y no hay colección seleccionada
  if (!presentation_id && !selectedCollectionId) {
    return <EmptyStateView />;
  }

  // Función para "Ir a seleccionar plantilla" desde las tarjetas de temas
  const handleGoToSelectTemplate = async (themeIndex: number) => {
    try {
      // Obtener el tema seleccionado
      const currentTheme = selectedCollectionId
        ? themeCollections?.find(c => c.id === selectedCollectionId)?.themes[themeIndex]
        : savedThemes?.[themeIndex];

      if (!currentTheme) {
        toast.error("No se pudo encontrar el tema seleccionado");
        return;
      }

      // Si no hay presentation_id, crear una nueva presentación con el contenido del tema
      if (!presentation_id) {
        console.log("No hay presentation_id, creando nueva presentación desde tema...");

        // Preparar el contenido del tema para crear la presentación
        const themeContent = currentTheme.presentation?.slides?.map(slide => slide.content).join('\n\n') || currentTheme.description;

        // Crear la presentación usando el API
        const createResponse = await PresentationGenerationApi.createPresentation({
          content: themeContent,
          n_slides: currentTheme.presentation?.slides?.length || 8,
          file_paths: [],
          language: "es", // Asumiendo español por el contenido del usuario
          tone: "professional",
          verbosity: "standard",
          instructions: `Crear presentación basada en el tema: ${currentTheme.title}`,
          include_table_of_contents: false,
          include_title_slide: true,
          web_search: false,
        });

        // Guardar el presentation_id generado
        dispatch(setPresentationId(createResponse.id));
        console.log("Nuevo presentation_id generado:", createResponse.id);
      }

      // Seleccionar el tema (esto actualizará los outlines)
      handleSelectThemeInCurrentContext(themeIndex);

      // Luego cambiar al tab de layouts
      setActiveTab(TABS.LAYOUTS);

      console.log("Tema seleccionado para generar presentación:", {
        themeIndex,
        themeTitle: currentTheme.title,
        slides: currentTheme?.presentation?.slides?.length || 0,
        selectedCollectionId,
        presentation_id: presentation_id || "Nuevo generado"
      });

      toast.success(`Tema "${currentTheme.title}" seleccionado. Ahora selecciona una plantilla.`);
    } catch (error: any) {
      console.error("Error al seleccionar tema:", error);
      toast.error("Error al seleccionar el tema", {
        description: error.message || "No se pudo procesar el tema seleccionado"
      });
    }
  };

  // Función para "Ir a la presentación" desde el tab de temas
  const handleGoToPresentationFromThemes = () => {
    console.log("Clic en 'Ir a la presentación'. presentation_id:", presentation_id);
    console.log("selectedLayoutGroup:", selectedLayoutGroup);

    if (!presentation_id) {
      toast.error("No hay presentación activa. Genera temas primero.");
      console.log("No hay presentation_id");
      return;
    }

    if (!selectedLayoutGroup) {
      toast.error("Primero selecciona una plantilla");
      console.log("No hay selectedLayoutGroup seleccionado");
      return;
    }

    console.log("selectedLayoutGroup encontrado:", {
      id: selectedLayoutGroup.id,
      name: selectedLayoutGroup.name,
      hasSlides: !!selectedLayoutGroup.slides,
      slidesCount: selectedLayoutGroup.slides?.length || 0
    });

    // Si el layout seleccionado es de preguntas, inyectar el contenido de la presentación
    if (selectedLayoutGroup.id.startsWith('questions-')) {
      const presentationContent = outlines.map(outline => outline.content).join('\n\n');

      // Modificar el layout para incluir el contenido de la presentación
      const modifiedLayoutGroup = {
        ...selectedLayoutGroup,
        slides: selectedLayoutGroup.slides?.map(slide => ({
          ...slide,
          data: {
            ...slide.data,
            presentationContent: presentationContent
          }
        }))
      };

      // Actualizar temporalmente el layout seleccionado
      setSelectedLayoutGroup(modifiedLayoutGroup);

      console.log("Contenido de presentación inyectado en layout de preguntas:", {
        contentLength: presentationContent.length,
        modifiedSlides: modifiedLayoutGroup.slides?.length
      });
    }

    // Si ya hay layout, generar la presentación directamente
    toast.success("Generando presentación...");
    handleSubmit();
  };

  return (
    <div className="h-[calc(100vh-72px)]">
      <OverlayLoader
        show={loadingState.isLoading}
        text={loadingState.message}
        showProgress={loadingState.showProgress}
        duration={loadingState.duration}
      />

      <Wrapper className="h-full flex flex-col w-full">
        <div className="flex-grow overflow-y-hidden w-[1200px] mx-auto">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
            <TabsList className="grid w-[75%] mx-auto my-4 grid-cols-3">
              <TabsTrigger value={TABS.OUTLINE}>Outline & Content</TabsTrigger>
              <TabsTrigger value={TABS.THEMES}>🎨 Temas</TabsTrigger>
              <TabsTrigger value={TABS.LAYOUTS}>Select Template</TabsTrigger>
            </TabsList>

            <div className="flex-grow w-full overflow-y-auto custom_scrollbar">
              <TabsContent value={TABS.OUTLINE}>
                <div>
                  <OutlineContent
                    outlines={outlines}
                    isLoading={streamState.isLoading}
                    isStreaming={streamState.isStreaming}
                    activeSlideIndex={streamState.activeSlideIndex}
                    highestActiveIndex={streamState.highestActiveIndex}
                    onDragEnd={handleDragEnd}
                    onAddSlide={handleAddSlide}
                  />
                </div>
              </TabsContent>

              <TabsContent value={TABS.THEMES}>
                <div>
                  <ThemesContent
                    themes={themes}
                    savedThemes={savedThemes}
                    selectedThemeIndex={selectedThemeIndex}
                    isLoading={themesLoading}
                    isStreaming={themesStreaming}
                    onSelectTheme={handleSelectThemeInCurrentContext}
                    onSaveThemesManually={handleSaveThemesManually}
                    onGoToSelectTemplate={handleGoToSelectTemplate}
                    themeCollections={themeCollections}
                    selectedCollectionId={selectedCollectionId}
                  />
                </div>
              </TabsContent>

              <TabsContent value={TABS.LAYOUTS}>
                <div>
                  <LayoutSelection
                    selectedLayoutGroup={selectedLayoutGroup}
                    onSelectLayoutGroup={setSelectedLayoutGroup}
                  />
                </div>
              </TabsContent>
            </div>
          </Tabs>
        </div>

        {/* Fixed Button */}
        <div className="py-4 border-t border-gray-200">
          <div className="max-w-[1200px] mx-auto">
            <GenerateButton
              loadingState={loadingState}
              streamState={{
                isStreaming: activeTab === TABS.OUTLINE ? streamState.isStreaming : false,
                isLoading: activeTab === TABS.OUTLINE ? streamState.isLoading : false
              }}
              selectedLayoutGroup={selectedLayoutGroup}
              onSubmit={handleSubmit}
              onGenerateThemes={handleGenerateThemes}
              themesStreaming={activeTab === TABS.THEMES ? themesStreaming : false}
              themesLoading={activeTab === TABS.THEMES ? themesLoading : false}
              showGoToPresentation={true}
              onGoToPresentation={handleGoToPresentationFromThemes}
              activeTab={activeTab}
            />
          </div>
        </div>
      </Wrapper>
    </div>
  );
};

export default OutlinePage;