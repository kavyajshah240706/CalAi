import os
import re

folders = [
    'ai_nutrition_scanner',
    'meal_history_logs',
    'nutriflow_chat',
    'nutriflow_dashboard',
    'profile_health_goals'
]

tailwind_config = """<script id="tailwind-config">
    tailwind.config = {
        darkMode: "class",
        theme: {
            extend: {
                colors: {
                    "surface-dim": "#f1f5f9",
                    "surface": "#f8fafc",
                    "on-surface": "#0f172a",
                    "on-surface-variant": "#475569",
                    "primary": "#10b981", 
                    "on-primary": "#ffffff",
                    "primary-container": "#d1fae5",
                    "on-primary-container": "#065f46",
                    "primary-fixed": "#34d399",
                    "primary-fixed-dim": "#059669",
                    "secondary": "#0ea5e9",
                    "on-secondary": "#ffffff",
                    "secondary-container": "#e0f2fe",
                    "on-secondary-container": "#0369a1",
                    "background": "#f8fafc",
                    "on-background": "#0f172a",
                    "surface-container-lowest": "#ffffff",
                    "surface-container-low": "#f8fafc",
                    "surface-container": "#f1f5f9",
                    "surface-container-high": "#e2e8f0",
                    "surface-container-highest": "#cbd5e1",
                    "outline": "#94a3b8",
                    "outline-variant": "#cbd5e1",
                    "error": "#ef4444",
                    "on-error": "#ffffff",
                    "error-container": "#fee2e2",
                    "on-error-container": "#991b1b",
                    "glass": "rgba(255, 255, 255, 0.7)"
                },
                fontFamily: {
                    "body-lg": ["Inter", "sans-serif"],
                    "body-md": ["Inter", "sans-serif"],
                    "body-sm": ["Inter", "sans-serif"],
                    "headline-xl": ["Manrope", "sans-serif"],
                    "headline-lg": ["Manrope", "sans-serif"],
                    "headline-md": ["Manrope", "sans-serif"],
                    "label-md": ["Inter", "sans-serif"],
                    "label-sm": ["Inter", "sans-serif"]
                },
                animation: {
                    'fade-in-up': 'fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards',
                    'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                },
                keyframes: {
                    fadeInUp: {
                        '0%': { opacity: '0', transform: 'translateY(20px)' },
                        '100%': { opacity: '1', transform: 'translateY(0)' },
                    }
                }
            }
        }
    }
</script>"""

global_styles = """<style>
    .material-symbols-outlined {
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    }
    .active-nav-item {
        color: #10b981 !important;
        font-weight: 700;
        background-color: rgba(16, 185, 129, 0.1);
        border-right: 4px solid #10b981;
    }
    .active-nav-item-mobile {
        color: #10b981 !important;
        font-weight: 700;
    }
    .glass-panel {
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    .hover-lift {
        transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease;
    }
    .hover-lift:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px -8px rgba(16, 185, 129, 0.25);
    }
    .scanner-line {
        width: 100%;
        height: 4px;
        background: #10b981;
        box-shadow: 0 0 15px #34d399, 0 0 30px #10b981;
        animation: scan 2s cubic-bezier(0.4, 0, 0.2, 1) infinite;
    }
    @keyframes scan {
        0% { transform: translateY(0) scaleY(0.5); opacity: 0; }
        10% { opacity: 1; scaleY(1); }
        90% { opacity: 1; scaleY(1); }
        100% { transform: translateY(220px) scaleY(0.5); opacity: 0; }
    }
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
</style>"""

nav_script = """
<script>
    // Automatically highlight active navigation
    document.addEventListener("DOMContentLoaded", () => {
        const path = window.location.pathname;
        const desktopLinks = document.querySelectorAll('nav.w-64 a');
        const mobileLinks = document.querySelectorAll('nav.fixed.bottom-0 a');
        
        const setActive = (links, className) => {
            links.forEach(link => {
                link.classList.remove('text-primary', 'font-bold', 'border-primary', 'bg-secondary-container/10', 'border-r-4');
                const href = link.getAttribute('href');
                if (href === '/' && path === '/') {
                    link.classList.add(className);
                } else if (href !== '/' && path.startsWith(href)) {
                    link.classList.add(className);
                }
            });
        };
        
        setActive(desktopLinks, 'active-nav-item');
        setActive(mobileLinks, 'active-nav-item-mobile');
    });
</script>
"""

desktop_nav = """<!-- SideNavBar -->
<nav class="h-screen w-64 fixed left-0 top-0 glass-panel shadow-[0px_4px_24px_rgba(0,0,0,0.06)] flex flex-col py-8 px-4 hidden md:flex z-50 animate-fade-in-up" style="animation-duration: 0.8s;">
    <div class="mb-8 px-2">
        <h1 class="font-headline-md text-headline-md font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">NutriFlow</h1>
        <p class="font-body-sm text-body-sm text-on-surface-variant font-medium mt-1">Premium Health AI</p>
    </div>
    <div class="flex-1 flex flex-col space-y-2">
        <a class="flex items-center space-x-3 px-4 py-3 rounded-lg text-on-surface-variant hover:text-primary hover:bg-surface-container transition-all duration-300" href="/">
            <span class="material-symbols-outlined">dashboard</span>
            <span class="font-label-md text-label-md">Dashboard</span>
        </a>
        <a class="flex items-center space-x-3 px-4 py-3 rounded-lg text-on-surface-variant hover:text-primary hover:bg-surface-container transition-all duration-300" href="/scanner">
            <span class="material-symbols-outlined">monochrome_photos</span>
            <span class="font-label-md text-label-md">AI Scanner</span>
        </a>
        <a class="flex items-center space-x-3 px-4 py-3 rounded-lg text-on-surface-variant hover:text-primary hover:bg-surface-container transition-all duration-300" href="/history">
            <span class="material-symbols-outlined">history</span>
            <span class="font-label-md text-label-md">History</span>
        </a>
        <a class="flex items-center space-x-3 px-4 py-3 rounded-lg text-on-surface-variant hover:text-primary hover:bg-surface-container transition-all duration-300" href="/chat">
            <span class="material-symbols-outlined">forum</span>
            <span class="font-label-md text-label-md">AI Chat</span>
        </a>
        <a class="flex items-center space-x-3 px-4 py-3 rounded-lg text-on-surface-variant hover:text-primary hover:bg-surface-container transition-all duration-300" href="/profile">
            <span class="material-symbols-outlined">person</span>
            <span class="font-label-md text-label-md">Settings</span>
        </a>
    </div>
    <a href="/scanner" class="w-full bg-gradient-to-r from-primary to-primary-fixed-dim text-on-primary py-3 rounded-xl shadow-lg shadow-primary/30 font-label-md text-label-md hover:scale-105 transition-all duration-300 mt-auto flex items-center justify-center no-underline">
        <span class="material-symbols-outlined mr-2 text-[20px]">add_circle</span> Log Meal
    </a>
</nav>"""

mobile_nav = """<!-- BottomNavBar (Mobile) -->
<nav class="fixed bottom-0 left-0 right-0 glass-panel shadow-[0px_-4px_24px_rgba(0,0,0,0.06)] md:hidden z-50 pb-safe">
    <div class="flex justify-around items-center h-16">
        <a class="flex flex-col items-center p-2 text-on-surface-variant hover:text-primary transition-colors" href="/">
            <span class="material-symbols-outlined text-[24px]">dashboard</span>
            <span class="font-label-sm text-[10px] mt-1 font-medium">Home</span>
        </a>
        <a class="flex flex-col items-center p-2 text-on-surface-variant hover:text-primary transition-colors" href="/history">
            <span class="material-symbols-outlined text-[24px]">history</span>
            <span class="font-label-sm text-[10px] mt-1 font-medium">History</span>
        </a>
        <div class="relative -top-5">
            <a href="/scanner" class="flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-tr from-primary to-primary-fixed-dim text-on-primary shadow-lg shadow-primary/40 hover:scale-110 transition-transform duration-300">
                <span class="material-symbols-outlined text-[28px]">add</span>
            </a>
        </div>
        <a class="flex flex-col items-center p-2 text-on-surface-variant hover:text-primary transition-colors" href="/chat">
            <span class="material-symbols-outlined text-[24px]">forum</span>
            <span class="font-label-sm text-[10px] mt-1 font-medium">AI Chat</span>
        </a>
        <a class="flex flex-col items-center p-2 text-on-surface-variant hover:text-primary transition-colors" href="/profile">
            <span class="material-symbols-outlined text-[24px]">person</span>
            <span class="font-label-sm text-[10px] mt-1 font-medium">Profile</span>
        </a>
    </div>
</nav>"""

for folder in folders:
    path = f"src/frontend/{folder}/code.html"
    if not os.path.exists(path):
        continue
        
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Replace tailwind-config
    content = re.sub(r'<script id="tailwind-config">.*?</script>', tailwind_config, content, flags=re.DOTALL)
    
    # Replace global styles
    content = re.sub(r'<style>.*?</style>', global_styles, content, flags=re.DOTALL)
    
    # Replace Desktop Nav
    # Find block starting with <!-- SideNavBar --> and ending with </nav>
    content = re.sub(r'<!-- SideNavBar -->.*?</nav>', desktop_nav, content, flags=re.DOTALL)
    
    # Replace Mobile Nav
    if "<!-- BottomNavBar (Mobile) -->" in content:
        content = re.sub(r'<!-- BottomNavBar \(Mobile\) -->.*?</nav>', mobile_nav, content, flags=re.DOTALL)
    else:
        # If it didn't exist, we must add it before </body>
        content = content.replace("</body>", f"{mobile_nav}\n</body>")
        
    # Inject Active Nav Script before </body>
    if "setActive(" not in content:
        content = content.replace("</body>", f"{nav_script}\n</body>")
        
    # Replace TopAppBar with glassmorphic topbar
    topbar_target = '<header class="fixed top-0 right-0 left-0 md:left-64 h-16 bg-surface-bright/80 backdrop-blur-md flex justify-between items-center px-margin-mobile md:px-margin-desktop z-40">'
    glass_topbar = '<header class="fixed top-0 right-0 left-0 md:left-64 h-16 glass-panel flex justify-between items-center px-4 md:px-8 z-40 animate-fade-in-up" style="animation-duration: 0.5s;">'
    content = content.replace(topbar_target, glass_topbar)
    
    # Also catch other topbar variations just in case
    content = re.sub(
        r'<header class="fixed top-0 right-0 left-0 md:left-64 h-16 bg-surface[^"]*".*?>',
        '<header class="fixed top-0 right-0 left-0 md:left-64 h-16 glass-panel flex justify-between items-center px-4 md:px-8 z-40 animate-fade-in-up" style="animation-duration: 0.5s;">',
        content
    )
    
    # Apply fade-in-up to main content wrappers
    content = content.replace('<div class="max-w-container-max mx-auto space-y-6">', '<div class="max-w-container-max mx-auto space-y-6 animate-fade-in-up" style="animation-delay: 0.1s; opacity: 0; animation-fill-mode: forwards;">')
    content = content.replace('<div class="max-w-container-max mx-auto w-full">', '<div class="max-w-container-max mx-auto w-full animate-fade-in-up" style="animation-delay: 0.1s; opacity: 0; animation-fill-mode: forwards;">')
    content = content.replace('<div class="max-w-2xl mx-auto w-full h-full flex flex-col pt-20 pb-24 md:pb-6 relative">', '<div class="max-w-2xl mx-auto w-full h-full flex flex-col pt-20 pb-24 md:pb-6 relative animate-fade-in-up" style="animation-delay: 0.1s; opacity: 0; animation-fill-mode: forwards;">')

    # Add hover-lift to cards
    content = content.replace('bg-surface-container-lowest rounded-xl p-4 shadow-[0px_4px_12px_rgba(0,0,0,0.03)]', 'bg-white rounded-2xl p-6 shadow-sm border border-surface-container-high hover-lift')
    content = content.replace('bg-surface-container-lowest rounded-xl shadow-[0px_4px_12px_rgba(0,0,0,0.03)] p-4', 'bg-white rounded-2xl p-6 shadow-sm border border-surface-container-high hover-lift')
    content = content.replace('bg-surface-container-lowest rounded-xl shadow-sm p-4', 'bg-white rounded-2xl p-6 shadow-sm border border-surface-container-high hover-lift')
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
        
print("UI Injection Complete!")
