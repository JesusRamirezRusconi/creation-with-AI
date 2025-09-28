import { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { toast } from "sonner";
import { setThemes, setSavedThemes } from "@/store/slices/presentationGeneration";
import { jsonrepair } from "jsonrepair";
import { RootState } from "@/store/store";

export const useThemesStreaming = (presentationId: string | null) => {
  const dispatch = useDispatch();
  const { themes, savedThemes } = useSelector((state: RootState) => state.presentationGeneration);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [activeThemeIndex, setActiveThemeIndex] = useState<number | null>(null);
  const [highestActiveIndex, setHighestActiveIndex] = useState<number>(-1);
  const prevThemesRef = useRef<any[]>([]);
  const activeIndexRef = useRef<number>(-1);
  const highestIndexRef = useRef<number>(-1);

  const startThemesGeneration = () => {
    if (!presentationId) return;

    let eventSource: EventSource;
    let accumulatedChunks = "";

    const initializeStream = async () => {
      setIsStreaming(true);
      setIsLoading(true);
      try {
        eventSource = new EventSource(
          `/api/v1/ppt/outlines/themes/stream/${presentationId}`
        );

        eventSource.addEventListener("response", (event) => {
          const data = JSON.parse(event.data);
          switch (data.type) {
            case "chunk":
              accumulatedChunks += data.chunk;
              try {
                const repairedJson = jsonrepair(accumulatedChunks);
                const partialData = JSON.parse(repairedJson);

                if (partialData.themes) {
                  const nextThemes: any[] = partialData.themes || [];
                  try {
                    // Solo actualizar el highestActiveIndex, no cambiar automáticamente la selección
                    const maxLen = Math.max(prevThemesRef.current?.length || 0, nextThemes.length);
                    if (maxLen - 1 > highestIndexRef.current) {
                      highestIndexRef.current = maxLen - 1;
                      setHighestActiveIndex(maxLen - 1);
                    }
                  } catch { }

                  prevThemesRef.current = nextThemes;
                  dispatch(setThemes(nextThemes));
                  setIsLoading(false);
                }
              } catch (error) {
                // JSON isn't complete yet, continue accumulating
              }
              break;

            case "complete":
              try {
                const themesData: any[] = data.themes.themes;
                dispatch(setThemes(themesData));

                // Solo guardar automáticamente si NO hay temas guardados previamente
                // Esto evita sobrescribir temas guardados existentes
                if (!savedThemes || savedThemes.length === 0) {
                  console.log("No hay temas guardados, guardando automáticamente los nuevos");
                  dispatch(setSavedThemes(themesData));
                } else {
                  console.log("Ya hay temas guardados, no se sobrescriben");
                }

                setIsStreaming(false);
                setIsLoading(false);
                setActiveThemeIndex(null);
                setHighestActiveIndex(-1);
                prevThemesRef.current = themesData;
                activeIndexRef.current = -1;
                highestIndexRef.current = -1;
                eventSource.close();
                toast.success("¡Temas generados exitosamente!");
              } catch (error) {
                console.error("Error parsing accumulated chunks:", error);
                toast.error("Failed to parse themes data");
                eventSource.close();
              }
              accumulatedChunks = "";
              break;

            case "closing":
              setIsStreaming(false);
              setIsLoading(false);
              setActiveThemeIndex(null);
              setHighestActiveIndex(-1);
              activeIndexRef.current = -1;
              highestIndexRef.current = -1;
              eventSource.close();
              break;

            case "error":
              setIsStreaming(false);
              setIsLoading(false);
              setActiveThemeIndex(null);
              setHighestActiveIndex(-1);
              activeIndexRef.current = -1;
              highestIndexRef.current = -1;
              eventSource.close();
              toast.error('Error generando temas',
                {
                  description: data.detail || 'Failed to connect to the server. Please try again.',
                }
              );
              break;
          }
        });

        eventSource.onerror = () => {
          setIsStreaming(false);
          setIsLoading(false);
          setActiveThemeIndex(null);
          setHighestActiveIndex(-1);
          activeIndexRef.current = -1;
          highestIndexRef.current = -1;
          eventSource.close();
          toast.error("Failed to connect to the server. Please try again.");
        };
      } catch (error) {
        setIsStreaming(false);
        setIsLoading(false);
        setActiveThemeIndex(null);
        setHighestActiveIndex(-1);
        activeIndexRef.current = -1;
        highestIndexRef.current = -1;
        toast.error("Failed to initialize connection");
      }
    };
    initializeStream();

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  };

  return {
    isStreaming,
    isLoading,
    activeThemeIndex,
    highestActiveIndex,
    startThemesGeneration,
    themes
  };
};
