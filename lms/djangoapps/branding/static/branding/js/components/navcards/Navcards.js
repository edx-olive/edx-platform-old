import React from 'react';
import PropTypes from 'prop-types';


const NavCardsListItem = (props) => {
    return (
        <li className="NavCardsListItem">
            <h2 className="NavCardsListItemTitle">{props.title}</h2>
            <div className="NavCardsListItemImage">
                <img src={props.image} />
            </div>
            <div className="NavCardsListItemDescription">
                <p>{props.description}</p>
            </div>
            <div className="NavCardsListItemLinkHolder">
                <a href={props.link} className="NavCardsListItemLink">Go to {props.name}</a>
            </div>
        </li>
    );
}

const NavCardsList = (props) => (
    <ul className="NavCardsList">
        {props.items.map((item, index) => {
            return <NavCardsListItem key={index} image={props.navcardsImgs[index]} {...item}/>;
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
