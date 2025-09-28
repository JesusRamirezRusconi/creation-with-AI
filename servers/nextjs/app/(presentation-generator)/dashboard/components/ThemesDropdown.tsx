"use client";

import React, { useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import { RootState } from "@/store/store";
import { selectTheme, setSavedThemes, selectThemeCollection } from "@/store/slices/presentationGeneration";
import { 
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Palette, CheckCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { trackEvent } from "@/utils/mixpanel";

const ThemesDropdown: React.FC = () => {
  const dispatch = useDispatch();
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const { savedThemes, selectedThemeIndex, presentation_id, themeCollections, selectedCollectionId } = useSelector(
    (state: RootState) => state.presentationGeneration
  );


  const handleSelectCollection = (collectionId: string, collectionName: string) => {
    dispatch(selectThemeCollection({ collectionId, themeIndex: 0 }));
    
    // Trackear evento
    trackEvent("collection_selected_from_header", {
      collectionId,
      collectionName
    });

    // Cerrar el popover
    setIsOpen(false);

    // Siempre ir al outline para ver los temas de la colección seleccionada
    // No necesitamos presentation_id para ver temas guardados
    router.push("/outline?tab=themes");
  };

  // Mantener función original para compatibilidad con temas individuales
  const handleSelectTheme = (themeIndex: number) => {
    dispatch(selectTheme({ themeIndex }));
    
    // Trackear evento
    trackEvent("theme_selected_from_header", {
      themeIndex,
      themeTitle: savedThemes[themeIndex]?.title
    });

    // Cerrar el popover
    setIsOpen(false);

    // Si no hay presentation_id activo, necesitamos crear uno nuevo o ir a upload
    if (!presentation_id) {
      // Navegar a upload para crear una nueva presentación con este tema
      router.push("/upload");
    } else {
      // Si ya hay una presentación activa, ir al outline
      router.push("/outline");
    }
  };

  // Debug: Log para verificar los temas
  console.log("ThemesDropdown Debug:", { savedThemes, length: savedThemes?.length });

  // Determinar qué mostrar: priorizar colecciones sobre temas individuales
  const hasCollections = themeCollections && themeCollections.length > 0;
  const hasIndividualThemes = savedThemes && savedThemes.length > 0;
  
  // Si no hay nada que mostrar, mostrar botón normal
  if (!hasCollections && !hasIndividualThemes) {
    return (
      <Button
        variant="ghost"
        className="flex items-center gap-2 px-3 py-2 text-white hover:bg-primary/80 rounded-md transition-colors outline-none"
        disabled
      >
        <Palette className="w-5 h-5" />
        <span className="text-sm font-medium font-inter">No hay temas</span>
      </Button>
    );
  }

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          className="flex items-center gap-2 px-3 py-2 text-white hover:bg-primary/80 rounded-md transition-colors outline-none"
        >
          <Palette className="w-5 h-5" />
          <span className="text-sm font-medium font-inter">Temas</span>
          {(hasCollections || hasIndividualThemes) && (
            <span className="text-xs bg-white/20 px-1.5 py-0.5 rounded-full">
              {hasCollections ? themeCollections!.length : savedThemes!.length}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-80 p-0">
        <div className="p-4 pb-2">
          <h3 className="text-base font-semibold text-gray-900">
            {hasCollections ? 'Colecciones de Temas' : 'Temas Guardados'}
          </h3>
        </div>
        <Separator />
        
        <div className="max-h-80 overflow-y-auto">
          {/* Mostrar colecciones si las hay */}
          {hasCollections && themeCollections!.map((collection) => (
            <div
              key={collection.id}
              onClick={() => handleSelectCollection(collection.id, collection.name)}
              className="cursor-pointer p-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
            >
              <div className="flex items-start gap-3 w-full">
                <div className="flex-shrink-0 mt-1">
                  {selectedCollectionId === collection.id ? (
                    <CheckCircle className="w-4 h-4 text-green-600" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border-2 border-gray-300" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-sm">📁 {collection.name}</span>
                    {selectedCollectionId === collection.id && (
                      <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                        Activa
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mb-1">
                    {collection.themes.length} subtemas disponibles
                  </p>
                  <p className="text-xs text-gray-400">
                    Guardado el {new Date(collection.savedAt).toLocaleDateString()}
                  </p>
                  {!presentation_id && (
                    <p className="text-xs text-blue-600 font-medium mt-1">
                      Crear nueva presentación
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}

          {/* Mostrar temas individuales si no hay colecciones pero sí temas individuales */}
          {!hasCollections && hasIndividualThemes && savedThemes!.map((theme, index) => (
            <div
              key={index}
              onClick={() => handleSelectTheme(index)}
              className="cursor-pointer p-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
            >
              <div className="flex items-start gap-3 w-full">
                <div className="flex-shrink-0 mt-1">
                  {selectedThemeIndex === index ? (
                    <CheckCircle className="w-4 h-4 text-green-600" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border-2 border-gray-300" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-sm">Tema {index + 1}</span>
                    {selectedThemeIndex === index && (
                      <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                        Activo
                      </span>
                    )}
                  </div>
                  <h4 className="font-semibold text-gray-900 text-sm truncate mb-1">
                    {theme.title}
                  </h4>
                  <p className="text-xs text-gray-500 line-clamp-2">
                    {theme.description}
                  </p>
                  <div className="flex items-center justify-between mt-1">
                    {theme.presentation?.slides && (
                      <p className="text-xs text-gray-400">
                        {theme.presentation.slides.length} diapositivas
                      </p>
                    )}
                    {!presentation_id && (
                      <p className="text-xs text-blue-600 font-medium">
                        Crear nueva presentación
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {!hasCollections && !hasIndividualThemes && (
            <div className="p-4 text-center text-gray-500">
              No hay temas guardados
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
};

export default ThemesDropdown;
