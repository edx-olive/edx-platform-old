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
                <Header pathname='/'></Header>
                <div className="MainHolder">
                    <div className="OnDemandDash">
                        <p>
                            Looking for ON DEMAND Dashboard? <a href="/dashboard">Click here</a>
                        </p>
                    </div>
                    <img className="Big-Logo-Img" src={logoImg} alt="appliedx"/>
                    <Navcards items={navcards}></Navcards>
                </div>
                <Footer></Footer>
            </div>
        );
    }
}
