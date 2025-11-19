import Link from "next/link"
import { Terminal } from "lucide-react"

export function Header() {
    return (
        <header className="sticky top-0 z-50 w-full border-b-2 border-black bg-white">
            <div className="container flex h-16 items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center border-2 border-black bg-black text-white">
                        <Terminal className="h-4 w-4" />
                    </div>
                    <span className="text-xl font-black tracking-tighter uppercase">
                        AI<span className="text-black">Today</span>
                    </span>
                </div>
            </div>
        </header>
    )
}
