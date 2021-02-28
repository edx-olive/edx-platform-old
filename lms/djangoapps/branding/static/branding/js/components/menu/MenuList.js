import React from 'react';

import MenuListItem from './MenuListItem';
import PropTypes from 'prop-types';


const MenuList = (props) => (
    <ul className={props.isOpen ? 'MenuList MenuList_open' : 'MenuList'}>
        {props.items.filter(item => item.inMenu).map((item, index) => {
            return <MenuListItem key={index} {...item} pathname={props.pathname} />;
        })}
    </ul>
);

MenuList.propTypes = {
    items: PropTypes.array.isRequired,
    isOpen: PropTypes.bool.isRequired,
    pathname: PropTypes.string.isRequired,
};

export default MenuList;
