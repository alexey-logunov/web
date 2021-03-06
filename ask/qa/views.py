from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView, CreateView
from .models import Question, Answer
from django.core.paginator import Paginator, EmptyPage
from .forms import AnswerForm, AskForm, SignUpForm, SignInForm, FeedBackForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth import login, authenticate
from django.core.mail import send_mail, BadHeaderError
from django.db.models import Q
from .utils import MyMixin


def test(request, *args, **kwargs):
    return HttpResponse('OK')


# class MainView(MyMixin, ListView):
class MainView(ListView):
    model = Question
    template_name = 'qa/index.html'
    context_object_name = 'questions'
    paginate_by = 10

    # queryset = Question.objects.select_related('author')
    # mixin_prop = 'hello, world!'

    def get_context_data(self, *, object_list=None, **kwargs):
        questions = super().get_context_data(**kwargs)
        questions['title'] = 'Главная страница'
        # questions['mixin_prop'] = self.get_prop()
        return questions

    def get_queryset(self):
        return Question.objects.new().select_related('author')


# class MainView(View):
#     def get(self, request, *args, **kwargs):
#         questions = Question.objects.new()
#         try:
#             limit = int(request.GET.get('limit', 10))
#         except ValueError:
#             limit = 10
#         if limit > 100:
#             limit = 10
#         try:
#             page_number = int(request.GET.get('page', 1))
#         except ValueError:
#             raise Http404
#         paginator = Paginator(questions, limit)
#         try:
#             page_obj = paginator.page(page_number)
#         except EmptyPage:
#             page_obj = paginator.page(paginator.num_pages)
#         paginator.baseurl = '/?page='
#         return render(request, 'qa/index.html', {
#             'questions': page_obj.object_list,
#             'paginator': paginator,
#             'page_obj': page_obj,
#         })


class PopularView(MainView):

    def get_queryset(self):
        return Question.objects.popular().prefetch_related('likes')


# class PopularView(View):
#     def get(self, request, *args, **kwargs):
#         questions = Question.objects.popular()
#         try:
#             limit = int(request.GET.get('limit', 10))
#         except ValueError:
#             limit = 10
#         if limit > 100:
#             limit = 10
#         try:
#             page = int(request.GET.get('page', 1))
#         except ValueError:
#             raise Http404
#         paginator = Paginator(questions, limit)
#         try:
#             page = paginator.page(page)
#         except EmptyPage:
#             page = paginator.page(paginator.num_pages)
#         paginator.baseurl = '/popular/?page='
#         return render(request, 'qa/popular.html', {
#             'questions': page.object_list,
#             'paginator': paginator,
#             'page': page,
#         })


# class QuestionView(DetailView):
#     model = Question
#     template_name = 'qa/question_details.html'
#     context_object_name = 'question_details'
#     allow_empty = False
#
#     # def get_context_data(self, *, object_list=None, **kwargs):
#     #     question_details = super().get_context_data(**kwargs)
#     #     question_details['title'] = Question.objects.get(pk=self.kwargs['question_id'])
#     #     return question_details
#     #
#     # def get_queryset(self):
#     #     return Question.objects.filter(pk=self.kwargs['question_id'])


class QuestionView(View):
    def get(self, request, pk, *args, **kwargs):
        question_details = get_object_or_404(Question, pk=pk)
        answers = question_details.answers.all()
        form = AnswerForm()
        return render(request, 'qa/question_details.html', {
            'question_details': question_details,
            'answers': answers,
            'form': form,
        })

    def post(self, request, pk, *args, **kwargs):
        form = AnswerForm(request.POST)
        if form.is_valid():
            text = request.POST['text']
            question_details = get_object_or_404(Question, pk=pk)
            author = self.request.user
            # print(form.cleaned_data)
            answer = Answer.objects.create(question_details=question_details, author=author, text=text)
            # answer = Answer.objects.create(**form.cleaned_data)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            # return redirect(answer)
            # answer = form.save()
            # url = answer.get_url()
            # return HttpResponseRedirect(url)
        return render(request, 'qa/question_details.html', {
            'form': form,
        })


# @login_required
# def answer_add(request):
#     if request.method == "POST":
#         # form = AnswerForm(request.user, request.POST)
#         form = AnswerForm(request.POST)
#         if form.is_valid():
#             # print(form.cleaned_data)
#             answer = Answer.objects.create(**form.cleaned_data)
#             return redirect(answer)
#             # answer = form.save()
#             # url = answer.get_url()
#             # return HttpResponseRedirect(url)
#     else:
#         form = AnswerForm()
#     return render(request, 'qa/answer_add.html', {
#         'form': form
#     })


class CreateQuestion(LoginRequiredMixin, CreateView):
    form_class = AskForm
    template_name = 'qa/question_add.html'
    # success_url = reverse_lazy('home')
    login_url = '/login/'
    # raise_exception = True


# @login_required
# def question_add(request):
#     if request.method == "POST":
#         # form = AskForm(request.user, request.POST)
#         form = AskForm(request.POST)
#         if form.is_valid():
#             # print(form.cleaned_data)
#             # question = Question.objects.create(**form.cleaned_data)
#             question = form.save()
#             return redirect(question)
#             # question = form.save()
#             # url = question.get_url()
#             # return HttpResponseRedirect(url)
#     else:
#         form = AskForm()
#     return render(request, 'qa/question_add.html', {
#         'form': form
#     })


class SignUpView(View):
    def get(self, request, *args, **kwargs):
        form = SignUpForm()
        return render(request, 'qa/signup.html', {
            'form': form,
        })

    def post(self, request, *args, **kwargs):
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user is not None:
                login(request, user)
                return HttpResponseRedirect('/')
        return render(request, 'qa/signup.html', {
            'form': form,
        })


class SignInView(View):
    def get(self, request, *args, **kwargs):
        form = SignInForm()
        return render(request, 'qa/login.html', {
            'form': form,
        })

    def post(self, request, *args, **kwargs):
        form = SignInForm(request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect('/')
        return render(request, 'qa/login.html', {
            'form': form,
        })


class FeedBackView(View):
    def get(self, request, *args, **kwargs):
        form = FeedBackForm()
        return render(request, 'qa/contact.html', {
            'form': form,
            'title': 'Написать мне'
        })

    def post(self, request, *args, **kwargs):
        form = FeedBackForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            from_email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            try:
                send_mail(f'От {name} | {subject}', message, from_email, ['al_logunov@mail.ru'])
            except BadHeaderError:
                return HttpResponse('Невалидный заголовок')
            return HttpResponseRedirect('success')
        return render(request, 'qa/contact.html', {
            'form': form,
        })

class SuccessView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'qa/success.html', {
            'title': 'Спасибо за обратную связь!'
        })

class SearchResultsView(View):
    def get(self, request, *args, **kwargs):
        query = self.request.GET.get('q')
        results = ""
        if query:
            results = Question.objects.filter(
                Q(title__icontains=query) | Q(text__icontains=query)
            )
        paginator = Paginator(results, 6)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'qa/search.html', {
            'title': 'Поиск',
            'results': page_obj,
            'count': paginator.count
        })