import { useState } from "react"
import Dashboard from "./pages/dashboard"
import Analytics from "./pages/analytics"
import Navbar from "./components/Navbar"
import "./App.css"

function App() {

    const [activeTab, setActiveTab] = useState("dashboard")

    return (
        <div className="app-shell">
            <div className="navbar-wrapper">
                <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
            </div>

            <div style={{ display: activeTab === "dashboard" ? "block" : "none" }}>
                <Dashboard />
            </div>
            <div style={{ display: activeTab === "analytics" ? "block" : "none" }}>
                <Analytics />
            </div>
        </div>
    )
}

export default App
