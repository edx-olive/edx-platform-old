import React from 'react';
import PropTypes from 'prop-types';


const defaultArgs = {
    target: '_blank',
    rel: 'noopener noreferrer',
    className: 'FooterList-Link'
};

const footerLinks = {
    section1: {
        name: 'About appliedX',
        links: [
            {
                name: 'LEARNING EXPERIENCES',
                url: 'http://team.amat.com/sites/appliedx/SitePages/appliedx-ON-DEMAND.aspx',
                args: defaultArgs,
                context: {}
            },
            {
                name: 'PATHWAY',
                url: 'https://team.amat.com/sites/CorpEngrPathway/',
                args: defaultArgs,
                context: {}
            },
            {
                name: 'CONNECT',
                url: 'http://team.amat.com/sites/CorpEngrappliedxCONNECT',
                args: defaultArgs,
                context: {}
            },
            {
                name: 'IMMERSIVE TECH',
                url: 'http://team.amat.com/sites/amaa/coevr/SitePages/Home.aspx',
                args: defaultArgs,
                context: {}
            }
        ]
    },
    section2: {
        name: 'Quick Links',
        links: [
            {
                name: 'AGU',
                url: 'http://agu/',
                args: defaultArgs,
                context: {}
            },
            {
                name: 'Create a course with appliedx',
                url: 'http://amat.service-now.com/help?id=sc_cat_item2&sys_id=c4d7dc2adbf29f003901f64eaf96199c',
                args: defaultArgs,
                context: {}
            },
            {
                name: 'Request to add a course to catalog',
                url: 'https://forms.office.com/Pages/ResponsePage.aspx?id=QyaccKmxFUStD1Ic-muj9fxLc-Gj9-tNgXR13-UPQpRUN0pVNFRZN1ZJMlY3WjJWVDJFVFc5SURYRC4u',
                args: defaultArgs,
                context: {}
            },
            {
                name: 'Classroom Schedule',
                url: 'http://amat.sabacloud.com/Saba/Web_spf/NA3P1PRD0037/common/calendar/',
                args: defaultArgs,
                context: {}
            }
        ]
    },
    section3: {
        name: 'Learner Support',
        links: [
            {
                name: 'FAQs',
                url: 'https://amat.service-now.com/help?id=help_kb_category&kb_category=bc6bcd14db8c9bc0df64dd90cf96193d',
                args: defaultArgs,
                context: {}
            },
            {
                name: 'Open a ticket',
                url: 'http://amat.service-now.com/help?id=help_kb_article&sys_id=08d4292ddb442f44df64dd90cf9619b7',
                args: defaultArgs,
                context: {}
            }
        ]
    }
};


const FooterBox = (props) => (
    <div className="Footer-Box">
        <strong className="Footer-Heading">{props.name}</strong>
        <ul className="FooterList">
            {props.links.map((item, idx) => (
                <li className="FooterList-Item" key={idx}>
                    <a href={item.url} {...item.args}>{item.name}</a>
                </li>
            ))}
        </ul>
    </div>
);


export class Footer extends React.Component {
    render() {
        return (
            <footer className="Footer" id="footer">
                <div className="Footer-Holder">
                    <FooterBox {...footerLinks.section1} />
                    <FooterBox {...footerLinks.section2} />
                    <FooterBox {...footerLinks.section3} />
                </div>
            </footer>
        );
    }
}


