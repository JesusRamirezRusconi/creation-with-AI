"use client";

import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FileText, Loader2, Sparkles, Save, BookmarkPlus, Layout } from "lucide-react";
import { usePathname } from "next/navigation";
import { trackEvent } from "@/utils/mixpanel";

interface Theme {
  title: string;
  description: string;
  presentation?: {
    slides?: Array<{
      content?: string;
    }>;
  };
  // Metadatos opcionales para temas guardados manualmente
  collectionName?: string;
  savedAt?: string;
  originalIndex?: number;
}

interface ThemeCollection {
  id: string;
  name: string;
  themes: Theme[];
  savedAt: string;
}

interface ThemesContentProps {
  themes: Theme[];
  savedThemes?: Theme[];
  selectedThemeIndex?: number | null;
  isLoading: boolean;
  isStreaming: boolean;
  onSelectTheme?: (themeIndex: number) => void;
  onSaveThemesManually?: (collectionName: string) => void;
  onGoToSelectTemplate?: (themeIndex: number) => void;
  themeCollections?: ThemeCollection[];
  selectedCollectionId?: string | null;
}

const ThemesContent: React.FC<ThemesContentProps> = ({
  themes,
  savedThemes,
  selectedThemeIndex,
  isLoading,
  isStreaming,
  onSelectTheme,
  onSaveThemesManually,
  onGoToSelectTemplate,
  themeCollections,
  selectedCollectionId
}) => {
  const pathname = usePathname();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [collectionName, setCollectionName] = useState("");

  const handleSaveManually = () => {
    if (collectionName.trim() && onSaveThemesManually) {
      onSaveThemesManually(collectionName.trim());
      setIsDialogOpen(false);
      setCollectionName("");
      trackEvent("themes_saved_manually", {
        pathname,
        collectionName: collectionName.trim(),
        themesCount: themes.length
      });
    }
  };

  if (isLoading && (!themes || themes.length === 0)) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Sparkles className="w-12 h-12 text-blue-500 mx-auto mb-4 animate-pulse" />
          <p className="text-lg font-medium text-gray-700 mb-2">Generando temas creativos...</p>
          <p className="text-sm text-gray-500">Estamos creando 10 perspectivas únicas para tu presentación</p>
        </div>
      </div>
    );
  }

  // Determinar qué temas mostrar basado en el contexto actual
  let themesToDisplay: Theme[] = [];
  let currentCollectionName = "";
  let showSavedThemes = false;

  if (selectedCollectionId && themeCollections) {
    // Si hay una colección seleccionada, mostrar los temas de esa colección
    const selectedCollection = themeCollections.find(c => c.id === selectedCollectionId);
    if (selectedCollection) {
      themesToDisplay = selectedCollection.themes;
      currentCollectionName = selectedCollection.name;
      showSavedThemes = true;
    }
  } else if (savedThemes && savedThemes.length > 0 && !isLoading && !isStreaming) {
    // Fallback al sistema anterior para compatibilidad
    themesToDisplay = savedThemes;
    showSavedThemes = true;
  } else {
    // Mostrar temas generados durante la generación o cuando no hay colecciones
    themesToDisplay = themes || [];
  }

  if (themesToDisplay && themesToDisplay.length > 0) {
    return (
      <div className="space-y-6 font-instrument_sans">
        {/* Header con información sobre temas guardados */}
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            🎨 {showSavedThemes ? (currentCollectionName ? `Colección: ${currentCollectionName}` : 'Temas Guardados') : 'Temas Generados'}
          </h2>
          <p className="text-gray-600">
            {showSavedThemes 
              ? 'Estos son los subtemas de tu colección. Puedes cambiar entre ellos.'
              : 'Selecciona el tema que mejor se adapte a tu presentación'
            }
          </p>
          
          {/* Botón para guardar temas manualmente */}
          {themes && themes.length > 0 && !isStreaming && !selectedCollectionId && (
            <div className="mt-4">
              <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogTrigger asChild>
                  <Button 
                    variant="outline" 
                    className="bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100"
                  >
                    <BookmarkPlus className="w-4 h-4 mr-2" />
                    Guardar Temas
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader>
                    <DialogTitle>Guardar Colección de Temas</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="collection-name">Nombre de la colección</Label>
                      <Input
                        id="collection-name"
                        placeholder="Ej: Presentación Empresa Q1"
                        value={collectionName}
                        onChange={(e) => setCollectionName(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleSaveManually();
                          }
                        }}
                      />
                    </div>
                    <p className="text-sm text-gray-500">
                      Se guardarán {themes.length} temas en esta colección
                    </p>
                  </div>
                  <div className="flex justify-end gap-3">
                    <Button
                      variant="outline"
                      onClick={() => setIsDialogOpen(false)}
                    >
                      Cancelar
                    </Button>
                    <Button
                      onClick={handleSaveManually}
                      disabled={!collectionName.trim()}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <Save className="w-4 h-4 mr-2" />
                      Guardar
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          )}
          
          {showSavedThemes && selectedThemeIndex !== null && (
            <div className="mt-2">
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                Tema activo: {selectedThemeIndex + 1}
              </Badge>
            </div>
          )}
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {themesToDisplay.map((theme, index) => {
            const isSelected = showSavedThemes && selectedThemeIndex === index;
            return (
              <Card key={index} className={`hover:shadow-lg transition-all duration-200 ${
                isSelected ? 'ring-2 ring-green-500 shadow-lg bg-green-50' : ''
              }`}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex gap-2 items-center">
                    <Badge variant="secondary" className="mb-2">
                      Tema {index + 1}
                    </Badge>
                    {isSelected && (
                      <Badge variant="default" className="mb-2 bg-green-600 text-white">
                        Activo
                      </Badge>
                    )}
                  </div>
                  {isStreaming && (
                    <div className="flex items-center text-sm text-blue-600">
                      <Loader2 className="h-4 w-4 animate-spin mr-1" />
                      Generando...
                    </div>
                  )}
                </div>
                <CardTitle className="text-lg leading-tight">
                  {theme.title}
                </CardTitle>
                <CardDescription className="text-sm">
                  {theme.description}
                </CardDescription>
              </CardHeader>

              <CardContent className="pt-0">
                  <div className="space-y-3">
                  <div className="text-sm text-gray-600">
                    <FileText className="w-4 h-4 inline mr-1" />
                    {theme.presentation?.slides?.length || 0} diapositivas
                  </div>

                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {theme.presentation?.slides?.slice(0, 3).map((slide, slideIndex) => (
                      <div key={slideIndex} className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                        <div className="font-medium">Diapositiva {slideIndex + 1}:</div>
                        <div className="truncate">
                          {(slide.content || '').replace(/[#*`]/g, '').substring(0, 60)}...
                        </div>
                      </div>
                    ))}
                    {theme.presentation?.slides && theme.presentation.slides.length > 3 && (
                      <div className="text-xs text-gray-400 text-center">
                        +{theme.presentation.slides.length - 3} más diapositivas
                      </div>
                    )}
                  </div>

                  <Button
                    onClick={() => {
                      trackEvent("theme_selected", {
                        pathname,
                        themeIndex: index,
                        themeTitle: theme.title
                      });
                      onSelectTheme?.(index);
                    }}
                    className={`w-full text-white ${
                      isSelected 
                        ? 'bg-gray-500 hover:bg-gray-600' 
                        : 'bg-[#10B981] hover:bg-[#10B981]/80'
                    }`}
                    size="sm"
                  >
                    {isSelected ? 'Tema seleccionado' : showSavedThemes ? 'Cambiar a este tema' : 'Seleccionar este tema'}
                  </Button>

                  {/* Nuevo botón: Ir a seleccionar plantilla */}
                  <Button
                    onClick={() => {
                      trackEvent("go_to_select_template", {
                        pathname,
                        themeIndex: index,
                        themeTitle: theme.title
                      });
                      onGoToSelectTemplate?.(index);
                    }}
                    variant="outline"
                    className="w-full border-blue-200 text-blue-700 hover:bg-blue-50"
                    size="sm"
                  >
                    <Layout className="w-4 h-4 mr-2" />
                    Ir a seleccionar plantilla
                  </Button>
                </div>
              </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="text-center py-12 bg-white rounded-lg border-2 border-dashed border-gray-200">
      <Sparkles className="w-12 h-12 text-gray-400 mx-auto mb-4" />
      <p className="text-gray-600 mb-4">
        Haz clic en "Temas" para generar 10 perspectivas creativas diferentes
      </p>
      <p className="text-sm text-gray-500">
        Cada tema tendrá su propia presentación completa con estructura única
      </p>
    </div>
  );
};

export default ThemesContent;
