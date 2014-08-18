from allauth.account.views import RedirectAuthenticatedUserMixin, CloseableSignupMixin, AjaxCapableProcessFormViewMixin, FormView
from account.forms import SignupForm

class SignupView(RedirectAuthenticatedUserMixin, CloseableSignupMixin,
				 AjaxCapableProcessFormViewMixin, FormView):
	template_name = "account/signup.html"
	form_class = SignupForm
	redirect_field_name = "next"
	success_url = None
	
	def get_success_url(self):
		# Explicitly passed ?next= URL takes precedence
		ret = (get_next_redirect_url(self.request, self.redirect_field_name) or self.success_url)
		return ret

	def form_valid(self, form):
		user = form.save(self.request)
		return complete_signup(self.request, user,
							   app_settings.EMAIL_VERIFICATION,
							   self.get_success_url())

	def get_context_data(self, **kwargs):
		form = kwargs['form']
		form.fields["email"].initial = self.request.session \
			.get('account_verified_email', None)
		ret = super(SignupView, self).get_context_data(**kwargs)
		login_url = passthrough_next_redirect_url(self.request,
												  reverse("account_login"),
												  self.redirect_field_name)
		redirect_field_name = self.redirect_field_name
		redirect_field_value = self.request.REQUEST.get(redirect_field_name)
		ret.update({"login_url": login_url,
					"redirect_field_name": redirect_field_name,
					"redirect_field_value": redirect_field_value})
		return ret

signup = SignupView.as_view()