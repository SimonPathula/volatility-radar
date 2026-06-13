import logo from "../assets/chart.png"
import "../styles/navbar.css"

function Navbar({ activeTab, setActiveTab }) {

    return (
        <div className="navbar">

            <div className="logo">

                <img
                    src={logo}
                    alt="Volatility Radar"
                    className="logo-icon"
                />

                <h1>
                    Volatility Radar
                </h1>

            </div>
            <div className="nav-links">
                <div className={
                        activeTab === "dashboard"
                        ? "nav-item active"
                        : "nav-item"
                    }
                    onClick={() =>
                        setActiveTab("dashboard")
                    }
                >
                        Dashboard
                </div>
                <div className={
                        activeTab === "analytics"
                        ? "nav-item active"
                        : "nav-item"
                    }
                    onClick={() =>
                        setActiveTab("analytics")
                    }
                >
                        Analytics
                </div>
            </div>
            <div className="placeholder"></div>

        </div>
    )
}

export default Navbar
