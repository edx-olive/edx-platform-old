import React from 'react';

import MenuList from '../components/menu/MenuList';
import UserPanel from '../components/user/UserPanel';
import routes from '../routes'

import PropTypes from 'prop-types';


class Header extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            'isMenuOpened': false,
            'scrollY': 0,
            'scrollDirection': 'top',
        };
        this.toggleMenu = this.toggleMenu.bind(this);
        this.handleScroll = this.handleScroll.bind(this);
        this.closePopup = this.closePopup.bind(this);
        this.escFunction = this.escFunction.bind(this);
    }

    async componentDidMount() {
        window.addEventListener('scroll', this.handleScroll);
        window.addEventListener('click', this.closePopup);
        window.addEventListener('keydown', this.escFunction);
    }

    componentWillUnmount() {
        window.removeEventListener('scroll', this.handleScroll);
        window.removeEventListener('keydown', this.escFunction);
    }

    handleScroll() {
        let scrollDirection;
        if (this.state.scrollY > window.pageYOffset) {
            scrollDirection = window.pageYOffset > 100 ? 'top' : 'less-top';
        } else {
            scrollDirection = window.pageYOffset > 100 ? 'bottom' : 'less-bottom';
        }
        this.setState({
            'scrollY': window.pageYOffset,
            'scrollDirection': scrollDirection,
        });
    }

    escFunction(e) {
        if (e.keyCode === 27) {
            this.closePopup(e);
        }
    }

    toggleMenu() {
        this.setState({
            'isMenuOpened': !this.state.isMenuOpened,
        });
    }

    closePopup(e) {
        this.userPanel && this.userPanel.closePopups(e);
    }

    render() {
        const { pathname } = this.props;

        const logoLinkAttrs = {rel: 'noopener noreferrer', className: 'Logo'};

        return (
            <header className={'Header Header_' + this.state.scrollDirection}>
                <div className="Header-Wrapper">
                    <div className="Logo-Wrapper">
                        <a href="/home" {...logoLinkAttrs}>
                            <img className="Logo-Img" src={this.props.logoImg} alt="appliedx"/>
                        </a>
                    </div>
                    <MenuList items={routes} isOpen={this.state.isMenuOpened} pathname={pathname}/>
                    <UserPanel/>
                    <div className="Opener-Holder">
                        <span className="Opener" onClick={this.toggleMenu}/>
                    </div>
                </div>
            </header>
        );
    }
}

Header.propTypes = {
    pathname: PropTypes.string.isRequired,
};

export default Header;
