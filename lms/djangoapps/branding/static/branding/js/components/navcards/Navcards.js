import React from 'react';
import PropTypes from 'prop-types';


const NavCardsListItem = (props) => {
    return <div className="NavCardsListItem">
        <div className="NavCardsListItemTitle">{props.title}</div>
        <div className="NavCardsListItemImage">{props.image}</div>
        <div className="NavCardsListItemDescription">{props.description}</div>
        <div className="NavCardsListItemLinkHolder">
            <a href={props.link} className="NavCardsListItemLink">Go to {props.name}</a>
        </div>
    </div>
}

const NavCardsList = (props) => (
    <ul className="NavCardsList">
        {props.items.map((item, index) => {
            return <NavCardsListItem key={index} {...item}/>;
        })}
    </ul>
);

NavCardsList.propTypes = {
    items: PropTypes.array.isRequired,
};

NavCardsListItem.propTypes = {
    title: PropTypes.string.isRequired,
    image: PropTypes.string.isRequired,
    description: PropTypes.string.isRequired,
    link: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
};

export default NavCardsList;
