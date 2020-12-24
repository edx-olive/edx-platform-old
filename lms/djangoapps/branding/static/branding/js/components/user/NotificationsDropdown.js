import React, {useRef, useEffect} from 'react';
import { TeamContext } from '../../context/Team';

const notificationsList = teamList => {
    return (
        <ul className="NotificationsDropdownList">
            {teamList.map((item, index) => (
                <li key={index} className="NotificationsDropdownList__item">
                    <div className="NotificationsDropdownList__image">
                        <img src={item.profileImage} alt="Profile Image" />
                    </div>
                    <div className="NotificationsDropdownList__body">
                        <div className="NotificationsDropdownList__name">
                            {item.employeeName}
                        </div>
                    </div>
                    <div className="NotificationsDropdownList__status">
                      <span className="NotificationsDropdownList__action">{item.status.tooltip}</span>
                    </div>
                </li>
            ))}
        </ul>
    )
};

const NotificationsDropdown = () => {
    const selfRef = useRef();
    const DropdownHandler = () => {
        const rect = selfRef.current.getBoundingClientRect();

        rect.bottom > window.innerHeight ?
        selfRef.current.classList.add('is-collapsed') :
        selfRef.current.classList.remove('is-collapsed')
    };

    useEffect(() => {
        window.addEventListener("load", DropdownHandler, true);
        window.addEventListener("resize", DropdownHandler, true);
    }, []);

    return (
        <div className="NotificationsDropdown" ref={selfRef}>
            <TeamContext.Consumer>
                {({team}) => (
                <div className="NotificationsDropdownHolder">
                    {team && notificationsList(team.teamList.reverse().slice(0, 3))}
                    <div className="NotificationsDropdownLink">
                        <a href="http://courses/manager/">See all notifications</a>
                    </div>
                </div>
                )}
            </TeamContext.Consumer>
        </div>
    );
}

export default NotificationsDropdown;
