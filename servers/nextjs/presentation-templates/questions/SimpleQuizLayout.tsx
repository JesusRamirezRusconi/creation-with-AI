import React, { useState, useEffect } from 'react'
import * as z from "zod";

export const layoutId = 'questions-simple-quiz'
export const layoutName = 'Cuestionario Simple'
export const layoutDescription = 'Layout simple con preguntas y respuestas sobre el contenido de la presentación.'

const simpleQuizSchema = z.object({
    presentationContent: z.string().optional().meta({
        description: "Contenido de la presentación para generar preguntas",
    }),
    title: z.string().min(5).max(50).default('Cuestionario de Evaluación').meta({
        description: "Título del cuestionario",
    })
})

export const Schema = simpleQuizSchema

export type SimpleQuizData = z.infer<typeof simpleQuizSchema>

interface Question {
    id: number;
    question: string;
    options: string[];
    correctAnswer: number;
}

interface SimpleQuizLayoutProps {
    data?: Partial<SimpleQuizData>
}

const SimpleQuizLayout: React.FC<SimpleQuizLayoutProps> = ({ data: slideData }) => {
    const [answers, setAnswers] = useState<number[]>([]);
    const [submitted, setSubmitted] = useState(false);

    const questions: Question[] = [
        {
            id: 1,
            question: "¿Cuál es el objetivo principal de la presentación?",
            options: ["Informar", "El objetivo principal", "Entretenir", "Vender"],
            correctAnswer: 1
        },
        {
            id: 2,
            question: "¿Qué concepto clave se presentó?",
            options: ["Concepto básico", "El concepto principal", "Tema secundario", "Conclusión"],
            correctAnswer: 1
        },
        {
            id: 3,
            question: "¿Cuál fue la conclusión principal?",
            options: ["Resumen", "La conclusión presentada", "Preguntas", "Agradecimientos"],
            correctAnswer: 1
        },
        {
            id: 4,
            question: "¿Qué recomendación se dio?",
            options: ["Recomendación general", "La recomendación específica", "Próximos pasos", "Contacto"],
            correctAnswer: 1
        },
        {
            id: 5,
            question: "¿Cuál es el beneficio principal mencionado?",
            options: ["Beneficio general", "El beneficio principal", "Características", "Ventajas"],
            correctAnswer: 1
        }
    ];

    useEffect(() => {
        setAnswers(new Array(questions.length).fill(-1));
    }, []);

    const handleAnswer = (questionIndex: number, answerIndex: number) => {
        const newAnswers = [...answers];
        newAnswers[questionIndex] = answerIndex;
        setAnswers(newAnswers);
    };

    const calculateScore = () => {
        return answers.reduce((score, answer, index) => {
            return score + (answer === questions[index].correctAnswer ? 1 : 0);
        }, 0);
    };

    const allAnswered = answers.every(answer => answer !== -1);
    const score = calculateScore();
    const percentage = (score / questions.length) * 100;

    return (
        <div className="min-h-screen bg-white p-8">
            <div className="max-w-4xl mx-auto">
                <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
                    {slideData?.title || 'Cuestionario de Evaluación'}
                </h1>

                {!submitted ? (
                    <div className="space-y-6">
                        {questions.map((question, qIndex) => (
                            <div key={question.id} className="bg-gray-50 p-6 rounded-lg">
                                <h3 className="text-lg font-semibold mb-4 text-gray-800">
                                    {qIndex + 1}. {question.question}
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    {question.options.map((option, oIndex) => (
                                        <button
                                            key={oIndex}
                                            onClick={() => handleAnswer(qIndex, oIndex)}
                                            className={`p-3 text-left rounded border-2 transition-all ${
                                                answers[qIndex] === oIndex
                                                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                                                    : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
                                            }`}
                                        >
                                            {option}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        ))}

                        <div className="text-center mt-8">
                            <button
                                onClick={() => setSubmitted(true)}
                                disabled={!allAnswered}
                                className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-lg font-semibold"
                            >
                                Enviar Respuestas
                            </button>
                            {!allAnswered && (
                                <p className="text-red-600 mt-2">
                                    Por favor responde todas las preguntas antes de enviar.
                                </p>
                            )}
                        </div>
                    </div>
                ) : (
                    <div className="text-center bg-gradient-to-r from-green-50 to-blue-50 p-8 rounded-lg">
                        <h2 className="text-2xl font-bold mb-4 text-gray-800">
                            ¡Evaluación Completada!
                        </h2>

                        <div className="text-6xl font-bold text-blue-600 mb-4">
                            {score}/{questions.length}
                        </div>

                        <div className="text-xl text-gray-700 mb-6">
                            Puntaje: {percentage.toFixed(0)}%
                        </div>

                        <div className="text-lg text-gray-600 mb-8">
                            {percentage >= 80 && "¡Excelente! Has comprendido muy bien el contenido."}
                            {percentage >= 60 && percentage < 80 && "¡Bien! Tienes un buen entendimiento."}
                            {percentage >= 40 && percentage < 60 && "Regular. Revisa algunos conceptos."}
                            {percentage < 40 && "Necesitas estudiar más el contenido."}
                        </div>

                        <button
                            onClick={() => {
                                setAnswers(new Array(questions.length).fill(-1));
                                setSubmitted(false);
                            }}
                            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 text-lg font-semibold"
                        >
                            Repetir Cuestionario
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default SimpleQuizLayout;
