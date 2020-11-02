import React from 'react';

import navcards from '../constants';
import Footer from './Footer';
import Header from './Header';
import Navcards from '../components/navcards/Navcards';

const logoImg = "/static/edx-theme/images/logo.png";

export class Homepage extends React.Component {
    constructor(props) {
        super(props);
    };
    render() {
        return (
            <div>
                <Header pathname='/home'></Header>
                <div className="MainHolder">
                    <div className="MainHolderWrapper">
                        <div className="OnDemandDash">
                            <p>
                                Looking for ON DEMAND Dashboard?
                            </p>
                            <a href="/dashboard">Click here</a>
                        </div>
                        <div className="Big-Logo-Img">
                            <img src={logoImg} alt="appliedx"/>
                        </div>
                        <Navcards items={navcards}></Navcards>
                    </div>
                </div>
                <Footer/>
            </div>
        );
    }
}
