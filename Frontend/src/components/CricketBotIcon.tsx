import React from 'react';

interface CricketBotIconProps {
    size?: number;
    className?: string;
}

const CricketBotIcon: React.FC<CricketBotIconProps> = ({ size = 24, className = "" }) => {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
        >
            {/* Robot Head */}
            <rect x="5" y="6" width="14" height="12" rx="2" strokeWidth="2" />

            {/* Antennae */}
            <path d="M9 6V3M15 6V3" />
            <circle cx="9" cy="2" r="0.5" fill="currentColor" />
            <circle cx="15" cy="2" r="0.5" fill="currentColor" />

            {/* Robot Eyes - Left eyes as a Cricket Ball */}
            <circle cx="9" cy="11" r="2" strokeWidth="1.5" />
            <path d="M8 9.5a2 2 0 0 1 2 0M8 12.5a2 2 0 0 0 2 0" strokeWidth="0.5" /> {/* Ball stitching */}

            <circle cx="15" cy="11" r="2" /> {/* Right Eye */}

            {/* Mouth */}
            <path d="M10 15h4" />

            {/* Cricket Bat - Leaning on the side */}
            <path
                d="M19 19l2-2M21 17l-3-8-2 2 3 8"
                strokeWidth="1.5"
                fill="none"
            />

            {/* Small ground line */}
            <path d="M4 22h16" strokeWidth="1" strokeOpacity="0.3" />
        </svg>
    );
};

export default CricketBotIcon;
