import React from 'react';
import PropTypes from 'prop-types';


const Icon = (props) => {
    const {className, name, onClick} = props;
    const click = onClick ? onClick : () => {};

    return <svg className={'Icon ' + (className ? className : '')} viewBox="0 0 24 24" onClick={click}>
        <use xlinkHref={`#${name}`}/>
    </svg>;
};


export default Icon;


Icon.propTypes = {
    name: PropTypes.string.isRequired,
    className: PropTypes.string,
    onClick: PropTypes.func
};
