<template>
    <md-layout md-gutter>
        <md-layout md-column md-gutter md-flex-xsmall="5" md-flex-small="5" md-flex-medium="10" md-flex-large="25"></md-layout>
        <md-layout md-column md-gutter md-flex-xsmall="90" md-flex-small="90" md-flex-medium="80" md-flex-large="50">
            <md-card class="clean-card">
                <md-card-area>
                    <md-card-header class="text-center">
                        <div class="m-xl text-center">
                            <img src="../../../static/logo_on_transparent.svg" width="50%">
                        </div>
                        <div class="md-subheading text-center">Welcome to InfraBox!</div>
                    </md-card-header>
                    <md-card-content class="m-xl" v-if="$store.state.settings.INFRABOX_ACCOUNT_SIGNUP_ENABLED || $store.state.settings.INFRABOX_ACCOUNT_LDAP_ENABLED">
                        <md-input-container :class="{'md-input-invalid': !mailValid}">
                            <md-input type="email" v-model="mail" name="email" @keyup.enter.native="login" required/>
                            <label>E-Mail</label>
                            <span v-if="!mailValid" class="md-error">Invalid E-Mail</span>
                        </md-input-container>
                        <md-input-container md-has-password :class="{'md-input-invalid': !pwValid}">
                            <label>Password</label>
                            <md-input type="password" v-model="password" name="password" @keyup.enter="login" required></md-input>
                            <span v-if="!pwValid" class="md-error">Invalid Password</span>
                        </md-input-container>
                        <md-button :disabled="!mailValid || !pwValid" class="md-raised md-primary" @click="login"><i class="fa fa-fw fa-sign-in"></i><span> Login</span></md-button>
                    </md-card-content>
                </md-card-area>
                <md-card-content class="m-xl" v-if="$store.state.settings.INFRABOX_GITHUB_ENABLED || $store.state.settings.INFRABOX_ACCOUNT_SIGNUP_ENABLED">
                    <h3 class="md-subheading">Don't have an InfraBox account?</h3>
                    <div class=" m-b-md"></div>
                    <md-button @click="loginGithub()"
                        v-if="$store.state.settings.INFRABOX_GITHUB_ENABLED"
                        md-theme="default"
                        class="md-raised md-primary">
                        <i class="fa fa-fw fa-github"></i>
                        <span> Login with GitHub</span>
                    </md-button>
                    <div v-if="$store.state.settings.INFRABOX_GITHUB_ENABLED && $store.state.settings.INFRABOX_ACCOUNT_SIGNUP_ENABLED">
                        <md-button disabled>or</md-button>
                    </div>
                    <md-button md-theme="default"
                        v-if="$store.state.settings.INFRABOX_ACCOUNT_SIGNUP_ENABLED"
                        @click="signup()"
                        class="md-raised md-primary">
                        <i class="fa fa-fw fa-user-plus"></i><span> Signup</span></md-button>
                </md-card-content>
            </md-card>
        </md-layout>
        <md-layout md-column md-gutter md-flex-xsmall="5" md-flex-small="5" md-flex-medium="10" md-flex-large="25"></md-layout>
    </md-layout>
</template>

<script>
import store from '../../store'
import router from '../../router'
import APIService from '../../services/APIService'
import UserService from '../../services/UserService'

export default {
    name: 'Login',
    store,
    data: () => ({
        mail: '',
        mailValid: false,
        password: '',
        pwValid: false
    }),
    watch: {
        mail () {
            // eslint-disable-next-line
            const emailRegex = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
            this.mailValid = emailRegex.test(this.mail)
        },
        password () {
            // eslint-disable-next-line
            const pwRegex = /^.{5,20}$/
            this.pwValid = pwRegex.test(this.password)
        }
    },
    methods: {
        loginGithub () {
            window.location.href = '/github/auth/'
        },
        signup () {
            console.log('signup')
            router.push('signup')
        },
        login () {
            APIService.post('account/login', {
                email: this.mail,
                password: this.password
            }).then(() => {
                UserService.login()
                router.push('/')
                location.reload()
            })
        }
    }
}
</script>

<style scoped>
</style>
