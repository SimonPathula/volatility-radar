import { useState } from "react"
import logo from "../assets/chart.png"
import "../styles/navbar.css"

function Navbar({ activeTab, setActiveTab }) {

    const [menuOpen, setMenuOpen] = useState(false)

    function handleNav(tab) {
        setActiveTab(tab)
        setMenuOpen(false)
    }

    return (
        <div className="navbar-container">

            <div className="navbar">

                <div className="logo">
                    <img
                        src={logo}
                        alt="Volatility Radar"
                        className="logo-icon"
                    />
                    <h1>Volatility Radar</h1>
                </div>

                <div className="nav-links">
                    <div
                        className={
                            activeTab === "dashboard"
                                ? "nav-item active"
                                : "nav-item"
                        }
                        onClick={() => handleNav("dashboard")}
                    >
                        Dashboard
                    </div>

                    <div
                        className={
                            activeTab === "analytics"
                                ? "nav-item active"
                                : "nav-item"
                        }
                        onClick={() => handleNav("analytics")}
                    >
                        Analytics
                    </div>
                </div>

                <div className="nav-right">

                    <a
                        href="https://www.linkedin.com/in/simon-pathula-91a710229/"
                        target="_blank"
                        rel="noreferrer"
                        className="author-link"
                    >
                        Author
                    </a>

                    <button
                        className="hamburger"
                        onClick={() => setMenuOpen(prev => !prev)}
                    >
                        <span />
                        <span />
                        <span />
                    </button>

                </div>

            </div>

            {menuOpen && (
                <div className="mobile-menu">

                    <div
                        className={
                            activeTab === "dashboard"
                                ? "mobile-nav-item active"
                                : "mobile-nav-item"
                        }
                        onClick={() => handleNav("dashboard")}
                    >
                        Dashboard
                    </div>

                    <div
                        className={
                            activeTab === "analytics"
                                ? "mobile-nav-item active"
                                : "mobile-nav-item"
                        }
                        onClick={() => handleNav("analytics")}
                    >
                        Analytics
                    </div>

                    <a
                        href="https://www.linkedin.com/in/simon-pathula-91a710229/"
                        target="_blank"
                        rel="noreferrer"
                        className="mobile-nav-item"
                        style={{
                            textDecoration: "none",
                            color: "#111"
                        }}
                    >
                        Author
                    </a>

                </div>
            )}

        </div>
    )
}

export default Navbar