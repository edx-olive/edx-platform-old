import React from 'react';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';

import { BrowserRouter } from 'react-router-dom';
import { mount } from 'enzyme/build';

import UserPanel from './UserPanel';
import {UserProfileContext} from '../../context/UserProfile';
import { USER_PROFILE_URL, NOTIFICATIONS_URL } from '../../api/urlPatterns';
import { userProfile } from '../../api/mock.constants';
import { fsmNotifications } from '../../setupTests';
import { NotificationsContext } from '../../context/Notifications';

const fetchMock = new MockAdapter(axios);


describe('<UserPanel />', () => {
    fetchMock.onGet(USER_PROFILE_URL.replace('%USER_ID%', 'bob@appliedx.org')).reply(200, {'userName': 'Bob'});
    fetchMock.onGet(NOTIFICATIONS_URL.replace('%USER_ID%', 'bob@appliedx.org')).reply(200, []);

    test('renders without crashing', () => {
        mount(
            <BrowserRouter>
                <UserProfileContext.Provider value={{profile: userProfile}}>
                    <NotificationsContext.Provider value={fsmNotifications}>
                        <UserPanel  />
                    </NotificationsContext.Provider>
                </UserProfileContext.Provider>
            </BrowserRouter>
        );
    });

});