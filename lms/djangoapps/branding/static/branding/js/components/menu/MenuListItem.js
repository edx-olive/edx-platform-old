import React from 'react';

import PropTypes from 'prop-types';


const MenuListItem = (props) => {
    const {path, pathname, title, args} = props;
    const isActive = (path === '/home' && pathname === path) ||
        (pathname.startsWith(path) && path !== '/') ||
        (pathname.startsWith('/manager/') && title === 'Dashboard');

        const linkArgs = Object.assign({}, args, { className: `MenuList-Link ${isActive ? 'MenuList-Link_active' : ''}` });

    return <li className="MenuList-Item">
                <a href={path} className={linkArgs.className}>{title}</a>
            </li>;
};

MenuListItem.propTypes = {
    title: PropTypes.string.isRequired,
    path: PropTypes.string.isRequired,
    pathname: PropTypes.string.isRequired,
    observable: PropTypes.bool,
    args: PropTypes.object,
    context: PropTypes.object
};

export default MenuListItem;
