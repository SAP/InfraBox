<template>
    <md-layout md-gutter>
        <md-layout md-column md-gutter md-flex-medium="10" md-flex-large="25" md-hide-xsmall md-hide-small></md-layout>
        <md-layout md-column md-gutter md-flex-medium="80" md-flex-large="50">
            <md-card class="clean-card">
                <md-card-area>
                    <md-card-header class="text-center">
                        <div class="m-xl text-center">
                            <img src="../../../static/logo_on_transparent.svg" width="50%">
                        </div>
                        <div class="md-subheading text-center">Welcome to InfraBox!</div>
                    </md-card-header>
                    <md-card-content class="m-xl" v-if="$store.state.settings.INFRABOX_ACCOUNT_SIGNUP_ENABLED">
                        <md-input-container :class="{'md-input-invalid': !mailValid}">
                            <md-input type="email" v-model="mail" name="email" required/>
                            <label>E-Mail</label>
                            <span v-if="!mailValid" class="md-error">Invalid E-Mail</span>
                        </md-input-container>
                        <md-input-container :class="{'md-input-invalid': !usernameValid}">
                            <md-input type="username" v-model="username" name="username" required/>
                            <label>Username</label>
                            <span v-if="!usernameValid" class="md-error">Invalid username</span>
                        </md-input-container>
                        <md-input-container md-has-password :class="{'md-input-invalid': !pwValid1}">
                            <label>Password</label>
                            <md-input type="password" v-model="password1" name="password1" required></md-input>
                            <span v-if="!pwValid1" class="md-error">Invalid Password</span>
                        </md-input-container>
                        <md-input-container md-has-password :class="{'md-input-invalid': !pwValid2}">
                            <label>Repeat Password</label>
                            <md-input type="password" v-model="password2" name="password2" required></md-input>
                            <span v-if="!pwValid2" class="md-error">Invalid Password</span>
                        </md-input-container>
                        <md-button :disabled="!usernameValid || !mailValid || !pwValid1 || !pwValid2" class="md-raised md-primary" @click="signup()"><i class="fa fa-fw fa-sign-in"></i><span> Signup</span></md-button>
                    </md-card-content>
                </md-card-area>
            </md-card>
        </md-layout>
        <md-layout md-column md-gutter md-flex-medium="10" md-flex-large="25" md-hide-xsmall md-hide-small></md-layout>
    </md-layout>
</template>

<script>
import store from '../../store'
import router from '../../router'
import NewAPIService from '../../services/NewAPIService'
import NotificationService from '../../services/NotificationService'
import Notification from '../../models/Notification'

export default {
    name: 'Signup',
    store,
    data: () => ({
        mail: '',
        mailValid: false,
        password1: '',
        password2: '',
        pwValid1: false,
        pwValid2: false,
        username: '',
        usernameValid: false
    }),
    watch: {
        mail () {
            // eslint-disable-next-line
            const emailRegex = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
            this.mailValid = emailRegex.test(this.mail)
        },
        username () {
            const userRegex = /^[A-Za-z0-9_-]{5,20}$/
            this.usernameValid = userRegex.test(this.username)
        },
        password1 () {
            // eslint-disable-next-line
            const pwRegex = /^.{5,20}$/
            this.pwValid1 = pwRegex.test(this.password1)
        },
        password2 () {
            // eslint-disable-next-line
            this.pwValid2 = this.password2 === this.password1
        }
    },
    methods: {
        signup () {
            NewAPIService.post('account/register', {
                email: this.mail,
                username: this.username,
                password1: this.password1,
                password2: this.password2
            }).then((message) => {
                router.push('/')
                location.reload()
            }).catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
        }
    }
}
</script>

<style scoped>
</style>
