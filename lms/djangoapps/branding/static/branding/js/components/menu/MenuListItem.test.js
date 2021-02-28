import React from 'react';
import { Route, BrowserRouter } from 'react-router-dom';

import {mount} from 'enzyme';

import MenuListItem from './MenuListItem';


describe('<MenuListItem />', () => {
    const initialEntries = ['/', '/two', {pathname: '/three'}];

    test('renders without crashing', () => {
        mount(<BrowserRouter initialEntries={initialEntries} initialIndex={0}>
            <Route path="/" render={() => (
                <MenuListItem pathname="/" path="/" title="Dashboard"/>
            )}/>
        </BrowserRouter>);
    });
});
