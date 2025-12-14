"use client"
import { Line } from "react-chartjs-2"
import { Card } from "@/components/ui/Card"

import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Tooltip,
    Legend,
} from "chart.js"

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

interface Dataset {
    label: string
    values: number[]
    borderColor: string
    backgroundColor: string
}

interface LineBaseProps {
    title: string
    labels: string[]
    datasets: Dataset[]
}

export default function LineBase({ title, labels, datasets }: LineBaseProps) {
    const data = {
        labels,
        datasets: datasets.map(dataset => ({
            label: dataset.label,
            data: dataset.values,
            borderColor: dataset.borderColor,
            backgroundColor: dataset.backgroundColor,
            tension: 0.4,
            fill: true,
        })),
    }

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: "top" as const,
            },
        },
        scales: {
            y: {
                beginAtZero: true,
            },
        },
    }

    return (
        <Card className="p-4 flex flex-col justify-center">
            <h2 className="text-base font-semibold">{title}</h2>

            <div className="flex items-center justify-center flex-1 min-h-[200px]">
                <div className="w-full max-w-lg h-[260px]">
                    <Line data={data} options={options} />
                </div>
            </div>
        </Card>
    )

}
