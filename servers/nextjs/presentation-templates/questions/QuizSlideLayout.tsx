import React, { useState, useEffect } from 'react'
import * as z from "zod";

export const layoutId = 'questions-quiz-slide'
export const layoutName = 'Evaluación de Conocimientos'
export const layoutDescription = 'Layout interactivo con 5 preguntas sobre el contenido de la presentación y cálculo de puntaje.'

const quizSlideSchema = z.object({
    presentationContent: z.string().default('').meta({
        description: "Contenido completo de la presentación para generar preguntas relevantes",
    }),
    title: z.string().min(5).max(50).default('Evaluación de Conocimientos').meta({
        description: "Título de la evaluación",
    }),
    description: z.string().min(10).max(200).default('Responde las siguientes preguntas para evaluar tu comprensión del contenido presentado.').meta({
        description: "Descripción de la evaluación",
    }),
    customQuestions: z.array(z.object({
        question: z.string(),
        options: z.array(z.string()),
        correctAnswer: z.number(),
        explanation: z.string()
    })).optional().meta({
        description: "Preguntas personalizadas (opcional)",
    })
})

export const Schema = quizSlideSchema

export type QuizSlideData = z.infer<typeof quizSlideSchema>

interface Question {
    id: number;
    question: string;
    options: string[];
    correctAnswer: number;
    explanation: string;
}

interface QuizSlideLayoutProps {
    data?: Partial<QuizSlideData>
}

const QuizSlideLayout: React.FC<QuizSlideLayoutProps> = ({ data: slideData }) => {
    const [currentQuestion, setCurrentQuestion] = useState(0);
    const [selectedAnswers, setSelectedAnswers] = useState<number[]>([]);
    const [showResults, setShowResults] = useState(false);
    const [questions, setQuestions] = useState<Question[]>([]);

    // Generar preguntas basadas en el contenido o usar preguntas personalizadas
    useEffect(() => {
        let questionsToUse: Question[];

        console.log("🔍 QuizSlideLayout - Datos recibidos:", {
            slideData,
            hasCustomQuestions: slideData?.customQuestions && slideData.customQuestions.length > 0,
            customQuestionsCount: slideData?.customQuestions ? slideData.customQuestions.length : 0,
            presentationContent: slideData?.presentationContent?.substring(0, 100) + "...",
            customQuestionsSample: slideData?.customQuestions?.[0] ? {
                question: slideData.customQuestions[0].question?.substring(0, 50) + "...",
                hasId: 'id' in slideData.customQuestions[0],
                optionsCount: slideData.customQuestions[0].options?.length
            } : null
        });

        // Si hay preguntas personalizadas, usarlas
        if (slideData?.customQuestions && slideData.customQuestions.length > 0) {
            console.log("✅ Usando preguntas personalizadas generadas por IA");
            questionsToUse = slideData.customQuestions.map((q, index) => ({
                id: (q as any).id || index + 1, // Usar el ID original si existe, o crear uno único
                question: q.question,
                options: q.options,
                correctAnswer: q.correctAnswer,
                explanation: q.explanation
            }));
        } else {
            console.log("⚠️ No hay preguntas personalizadas, usando preguntas genéricas");
            // Generar preguntas basadas en el contenido de la presentación
            const content = slideData?.presentationContent || '';

            // Extraer información clave del contenido para generar preguntas más relevantes
            const hasContent = content.length > 0;

            questionsToUse = [
                {
                    id: 1,
                    question: hasContent
                        ? "¿Cuál es el tema principal abordado en esta presentación?"
                        : "¿Cuál es el objetivo principal de la presentación?",
                    options: hasContent
                        ? [
                            "Desarrollo técnico",
                            "El tema principal presentado",
                            "Gestión operativa",
                            "Análisis estratégico"
                        ]
                        : [
                            "Informar sobre un tema",
                            "El objetivo principal",
                            "Entretenir al público",
                            "Vender un producto"
                        ],
                    correctAnswer: 1,
                    explanation: hasContent
                        ? "El tema principal se menciona claramente en la introducción y se desarrolla a lo largo de la presentación."
                        : "El objetivo principal guía toda la estructura de la presentación."
                },
                {
                    id: 2,
                    question: hasContent
                        ? "¿Qué concepto clave se explica en detalle?"
                        : "¿Qué concepto fundamental se presenta?",
                    options: hasContent
                        ? [
                            "Concepto básico",
                            "El concepto clave explicado",
                            "Tema secundario",
                            "Aspecto técnico"
                        ]
                        : [
                            "Idea general",
                            "El concepto fundamental",
                            "Tema complementario",
                            "Detalle específico"
                        ],
                    correctAnswer: 1,
                    explanation: hasContent
                        ? "Este concepto se desarrolla con detalle en varios slides de la presentación."
                        : "El concepto fundamental es la base de toda la presentación."
                },
                {
                    id: 3,
                    question: hasContent
                        ? "¿Cuál es la conclusión principal presentada?"
                        : "¿Cuál es la conclusión más importante?",
                    options: hasContent
                        ? [
                            "Resumen general",
                            "La conclusión principal",
                            "Preguntas abiertas",
                            "Agradecimientos finales"
                        ]
                        : [
                            "Resumen del tema",
                            "La conclusión principal",
                            "Preguntas del público",
                            "Cierre de la presentación"
                        ],
                    correctAnswer: 1,
                    explanation: hasContent
                        ? "La conclusión se presenta al final y resume los puntos más importantes."
                        : "La conclusión sintetiza los aspectos más relevantes presentados."
                },
                {
                    id: 4,
                    question: hasContent
                        ? "¿Qué beneficio o ventaja se destaca?"
                        : "¿Qué beneficio se menciona?",
                    options: hasContent
                        ? [
                            "Ventaja general",
                            "El beneficio destacado",
                            "Característica técnica",
                            "Aspecto operativo"
                        ]
                        : [
                            "Beneficio común",
                            "El beneficio específico",
                            "Característica destacada",
                            "Aspecto funcional"
                        ],
                    correctAnswer: 1,
                    explanation: hasContent
                        ? "Este beneficio se destaca específicamente en la presentación como un punto clave."
                        : "El beneficio mencionado es uno de los puntos más importantes para el público."
                },
                {
                    id: 5,
                    question: hasContent
                        ? "¿Cuál es la recomendación o acción sugerida?"
                        : "¿Qué acción se recomienda?",
                    options: hasContent
                        ? [
                            "Acción general",
                            "La recomendación específica",
                            "Implementación técnica",
                            "Evaluación posterior"
                        ]
                        : [
                            "Acción inmediata",
                            "La recomendación principal",
                            "Siguiente paso técnico",
                            "Análisis posterior"
                        ],
                    correctAnswer: 1,
                    explanation: hasContent
                        ? "La recomendación se presenta como el siguiente paso lógico después del contenido mostrado."
                        : "La recomendación es la acción concreta que se sugiere al finalizar."
                }
            ];
        }

        // Solo actualizar si las preguntas realmente cambiaron para evitar re-renders innecesarios
        setQuestions(prevQuestions => {
            const questionsChanged = JSON.stringify(prevQuestions) !== JSON.stringify(questionsToUse);
            if (questionsChanged) {
                console.log("🔄 Actualizando preguntas del quiz");
                return questionsToUse;
            }
            return prevQuestions;
        });

        // Resetear respuestas solo si cambió el número de preguntas
        setSelectedAnswers(prevAnswers => {
            if (prevAnswers.length !== questionsToUse.length) {
                return new Array(questionsToUse.length).fill(-1);
            }
            return prevAnswers;
        });
    }, [slideData]);

    const handleAnswerSelect = (questionIndex: number, answerIndex: number) => {
        const newAnswers = [...selectedAnswers];
        newAnswers[questionIndex] = answerIndex;
        setSelectedAnswers(newAnswers);
    };

    const calculateScore = () => {
        let correct = 0;
        questions.forEach((question, index) => {
            if (selectedAnswers[index] === question.correctAnswer) {
                correct++;
            }
        });
        return correct;
    };

    const getScoreMessage = (score: number) => {
        const percentage = (score / questions.length) * 100;
        if (percentage >= 80) return "¡Excelente! Has comprendido muy bien el contenido.";
        if (percentage >= 60) return "¡Bien! Tienes un buen entendimiento del tema.";
        if (percentage >= 40) return "Regular. Te recomendamos revisar algunos conceptos.";
        return "Necesitas estudiar más el contenido presentado.";
    };

    const canFinishQuiz = selectedAnswers.every(answer => answer !== -1);

    if (questions.length === 0) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Generando preguntas...</p>
                </div>
            </div>
        );
    }

    if (showResults) {
        const score = calculateScore();
        const percentage = (score / questions.length) * 100;

        return (
            <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 p-8">
                <div className="max-w-2xl mx-auto">
                    <div className="bg-white rounded-xl shadow-lg p-8 text-center">
                        <h1 className="text-3xl font-bold text-gray-800 mb-4">
                            Resultados de la Evaluación
                        </h1>

                        <div className="mb-8">
                            <div className="text-6xl font-bold text-blue-600 mb-2">
                                {score}/{questions.length}
                            </div>
                            <div className="text-xl text-gray-600 mb-4">
                                {percentage.toFixed(0)}% de aciertos
                            </div>
                            <p className="text-lg text-gray-700">
                                {getScoreMessage(score)}
                            </p>
                        </div>

                        <div className="bg-gray-50 rounded-lg p-6 mb-6">
                            <h3 className="text-lg font-semibold mb-4">Resumen de respuestas:</h3>
                            <div className="space-y-2">
                                {questions.map((question, index) => (
                                    <div key={`result-${question.id}`} className="flex items-center justify-between">
                                        <span className="text-sm">Pregunta {index + 1}:</span>
                                        <span className={`text-sm font-medium ${
                                            selectedAnswers[index] === question.correctAnswer
                                                ? 'text-green-600'
                                                : 'text-red-600'
                                        }`}>
                                            {selectedAnswers[index] === question.correctAnswer ? '✓ Correcta' : '✗ Incorrecta'}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <button
                            onClick={() => {
                                // Reset state de manera estable
                                setCurrentQuestion(0);
                                setSelectedAnswers(new Array(questions.length).fill(-1));
                                setShowResults(false);
                            }}
                            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            Repetir Evaluación
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    const currentQ = questions[currentQuestion];
    const progress = ((currentQuestion + 1) / questions.length) * 100;

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
            <div className="max-w-2xl mx-auto">
                {/* Header */}
                <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                    <div className="flex justify-between items-center mb-4">
                        <h1 className="text-2xl font-bold text-gray-800">
                            {slideData?.title || 'Evaluación de Conocimientos'}
                        </h1>
                        <span className="text-sm text-gray-500">
                            Pregunta {currentQuestion + 1} de {questions.length}
                        </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                        <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${progress}%` }}
                        ></div>
                    </div>

                    <p className="text-gray-600">
                        {slideData?.description || 'Responde las siguientes preguntas para evaluar tu comprensión del contenido presentado.'}
                    </p>
                </div>

                {/* Question Card */}
                <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                    <h2 className="text-xl font-semibold text-gray-800 mb-6">
                        {currentQ.question}
                    </h2>

                    <div className="space-y-3">
                        {currentQ.options.map((option, index) => (
                            <button
                                key={`question-${currentQuestion}-option-${index}`}
                                onClick={() => handleAnswerSelect(currentQuestion, index)}
                                className={`w-full p-4 text-left rounded-lg border-2 transition-all ${
                                    selectedAnswers[currentQuestion] === index
                                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                                }`}
                            >
                                <div className="flex items-center">
                                    <div className={`w-4 h-4 rounded-full border-2 mr-3 ${
                                        selectedAnswers[currentQuestion] === index
                                            ? 'border-blue-500 bg-blue-500'
                                            : 'border-gray-300'
                                    }`}>
                                        {selectedAnswers[currentQuestion] === index && (
                                            <div className="w-2 h-2 bg-white rounded-full mx-auto mt-0.5"></div>
                                        )}
                                    </div>
                                    <span className="text-gray-700">{option}</span>
                                </div>
                            </button>
                        ))}
                    </div>

                    {selectedAnswers[currentQuestion] !== -1 && (
                        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                            <p className="text-sm text-blue-800">
                                <strong>Explicación:</strong> {currentQ.explanation}
                            </p>
                        </div>
                    )}
                </div>

                {/* Navigation */}
                <div className="flex justify-between">
                    <button
                        onClick={() => setCurrentQuestion(Math.max(0, currentQuestion - 1))}
                        disabled={currentQuestion === 0}
                        className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Anterior
                    </button>

                    {currentQuestion < questions.length - 1 ? (
                        <button
                            onClick={() => setCurrentQuestion(currentQuestion + 1)}
                            disabled={selectedAnswers[currentQuestion] === -1}
                            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Siguiente
                        </button>
                    ) : (
                        <button
                            onClick={() => setShowResults(true)}
                            disabled={!canFinishQuiz}
                            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Finalizar Evaluación
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default QuizSlideLayout;