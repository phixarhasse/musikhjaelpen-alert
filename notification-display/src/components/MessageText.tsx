import React from 'react';
import '../styles/fonts.css';

interface MessageTextProps {
    message: string;
}

const MessageText: React.FC<MessageTextProps> = ({ message }) => {
    const paragraphStyle = {
        color: '#F46607',
        fontFamily: 'Ethnocentric Regular Italic',
    };

    return <p style={paragraphStyle}>{message}</p>;
};

export default MessageText;
