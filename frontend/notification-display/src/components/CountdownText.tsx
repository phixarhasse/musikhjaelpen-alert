import React from 'react';

interface CountdownTextProps {
    count: number;
}

const CountdownText: React.FC<CountdownTextProps> = ({ count }) => {
    const paragraphStyle = {
        color: '#ff0000',
        fontFamily: 'Courier',
        fontWeight: 'bold'
    };

    return <p style={paragraphStyle}>Countdown: {count}</p>;
};

export default CountdownText;
