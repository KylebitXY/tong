from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView, ListView
from .forms import *
from .models import Athlete, Coach, Staff, Media, RoleType, Category, Country, Belt, Team, Membership, Tournament, TournamentParticipation
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from main1.utils import *
from django.conf import settings
from django.core.files.storage import default_storage
import os
from django.contrib import messages
import logging
from django.http import HttpResponse
from fillpdf import fillpdfs
from reportlab.pdfgen import canvas  # or your PDF library

import datetime
from .utils import *

from docx import Document
from docx2pdf import convert  
logger = logging.getLogger(__name__)

@login_required
def coach_dashboard(request):
    try:
        # Get the coach associated with the logged-in user
        coach = Coach.objects.get(user=request.user)
        
        # Filter active athletes for the coach
        active_athletes = Athlete.objects.filter(coach=coach, is_active=True)
        
        # Get upcoming tournaments
        upcoming_tournaments = Tournament.objects.filter(start_date__gte=datetime.date.today()).order_by('start_date')

        # Prepare context with relevant data
        context = {
            'active_athletes': active_athletes,
            'coach': coach,
            'upcoming_tournaments': upcoming_tournaments,  # Include upcoming tournaments
        }
        
        # Render the coach dashboard template
        return render(request, 'index1.html', context)
    
    except Coach.DoesNotExist:
        # Handle the case where no coach is found for the logged-in user
        return render(request, 'no_coach.html', {'message': 'You are not assigned as a coach.'})


@login_required
def register_athletes(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)

    # Athletes NOT yet registered in this tournament
    registered_ids = TournamentParticipation.objects.filter(
        tournament=tournament
    ).values_list('athlete_id', flat=True)

    athletes = Athlete.objects.exclude(id__in=registered_ids)

    categories = Category.objects.all()

    # REGISTER EXISTING ATHLETE INTO TOURNAMENT
    if request.method == "POST" and 'athlete_id' in request.POST:
        athlete = get_object_or_404(Athlete, id=request.POST.get('athlete_id'))
        selected_categories = request.POST.getlist('category')

        participation, _ = TournamentParticipation.objects.get_or_create(
            tournament=tournament,
            athlete=athlete
        )
        participation.category.set(selected_categories)

        return redirect('register_athletes', tournament_id=tournament.id)

    # REGISTER NEW ATHLETE FIRST
    athlete_form = AthleteForm()

    return render(request, 'tournament/register_athletes.html', {
        'tournament': tournament,
        'athletes': athletes,
        'categories': categories,
        'athlete_form': athlete_form
    })

# Athlete Views
@method_decorator(login_required, name='dispatch')
class AthleteListView(LoginRequiredMixin, ListView):
    model = Athlete
    template_name = 'athletes/athlete_list.html'
    context_object_name = 'athletes'

    def get_queryset(self):
        athletes = Athlete.objects.select_related('country', 'belt', 'accommodation').prefetch_related('category')
        coach_athletes = Coach.objects.filter(is_athlete=True).select_related('country', 'belt').prefetch_related('category')

        athletes_list = []
        for athlete in athletes:
            athlete_data = {
                'pk': athlete.pk,
                'name': athlete.name,
                'passport_photo': athlete.passport_photo.url if athlete.passport_photo else None,
                'country': athlete.country.name,
                'region': athlete.region.name if athlete.region else 'N/A',
                'id_passport_number': athlete.id_passport_number,
                'passport': athlete.passport,
                'dob': athlete.dob,
                'gender': athlete.gender,
                'contacts': athlete.contacts,
                'arrival_date': athlete.arrival_date,
                'departure_date': athlete.departure_date,
                'accommodation': athlete.accommodation.name if athlete.accommodation else 'N/A',
                'weight': athlete.weight,
                'belt': athlete.belt.name if athlete.belt else 'N/A',
                'category': list(athlete.category.values_list('name', flat=True)),
                'age': athlete.age,
                'get_weight_category': athlete.get_weight_category,
            }
            athletes_list.append(athlete_data)

        for coach in coach_athletes:
            coach_data = {
                'pk': coach.pk,
                'name': coach.name,
                'passport_photo': coach.passport_photo.url if coach.passport_photo else None,
                'country': coach.country.name,
                'region': coach.region.name if coach.region else 'N/A',
                'id_passport_number': coach.id_passport_number,
                'passport': coach.passport,
                'dob': coach.dob,
                'gender': coach.gender,
                'contacts': coach.contacts,
                'arrival_date': coach.arrival_date,
                'departure_date': coach.departure_date,
                'accommodation': coach.accommodation.name if coach.accommodation else 'N/A',
                'weight': coach.weight,
                'belt': coach.belt.name if coach.belt else 'N/A',
                'category': list(coach.category.values_list('name', flat=True)),
                'age': coach.age,
                'get_weight_category': coach.get_weight_category,
            }
            athletes_list.append(coach_data)

        return athletes_list

@method_decorator(login_required, name='dispatch')
class AthleteDetailView(DetailView):
    model = Athlete
    template_name = 'athletes/athlete_detail.html'
    context_object_name = 'athlete'

@method_decorator(login_required, name='dispatch')
class AthleteCreateView(CreateView):
    model = Athlete
    form_class = AthleteForm
    template_name = 'athletes/athlete_form.html'

    def get_success_url(self):
        tournament_id = self.request.GET.get('tournament')
        if tournament_id:
            return reverse('register_athletes', args=[tournament_id])
        return reverse('athlete_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.category.set(form.cleaned_data['category'])
        return response


@method_decorator(login_required, name='dispatch')
class AthleteUpdateView(UpdateView):
    model = Athlete
    form_class = AthleteUpdateForm
    template_name = 'athletes/update.html'
    success_url = reverse_lazy('athlete_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.category.set(form.cleaned_data['category'])
        return response

@method_decorator(login_required, name='dispatch')
class AthleteDeleteView(DeleteView):
    model = Athlete
    template_name = 'athletes/athlete_confirm_delete.html'
    success_url = reverse_lazy('athlete_list')

# Coach Views
@method_decorator(login_required, name='dispatch')
class CoachListView(ListView):
    model = Coach
    template_name = 'coach/coach_list.html'
    context_object_name = 'coaches'

@method_decorator(login_required, name='dispatch')
class CoachDetailView(DetailView):
    model = Coach
    template_name = 'coach/coach_detail.html'
    context_object_name = 'coach'

@method_decorator(login_required, name='dispatch')
class CoachCreateView(CreateView):
    model = Coach
    form_class = CoachForm
    template_name = 'coach/coach_form.html'
    success_url = reverse_lazy('coach_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.category.set(form.cleaned_data['category'])
        return response

@method_decorator(login_required, name='dispatch')
class CoachUpdateView(UpdateView):
    model = Coach
    form_class = CoachForm
    template_name = 'coach/coach_update.html'
    success_url = reverse_lazy('coach_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.category.set(form.cleaned_data['category'])
        return response

@method_decorator(login_required, name='dispatch')
class CoachDeleteView(DeleteView):
    model = Coach
    template_name = 'coach/coach_confirm_delete.html'
    success_url = reverse_lazy('coach_list')

# Staff Views
@method_decorator(login_required, name='dispatch')
class StaffListView(ListView):
    model = Staff
    template_name = 'staff/staff_list.html'
    context_object_name = 'staff_members'

@method_decorator(login_required, name='dispatch')
class StaffDetailView(DetailView):
    model = Staff
    template_name = 'staff/staff_detail.html'
    context_object_name = 'staff'

@method_decorator(login_required, name='dispatch')
class StaffCreateView(CreateView):
    model = Staff
    form_class = StaffForm
    template_name = 'staff/staff_form.html'
    success_url = reverse_lazy('staff_list')

@method_decorator(login_required, name='dispatch')
class StaffUpdateView(UpdateView):
    model = Staff
    form_class = StaffForm
    template_name = 'staff/staff_update.html'
    success_url = reverse_lazy('staff_list')

@method_decorator(login_required, name='dispatch')
class StaffDeleteView(DeleteView):
    model = Staff
    template_name = 'staff/staff_confirm_delete.html'
    success_url = reverse_lazy('staff_list')

# Media Views
@method_decorator(login_required, name='dispatch')
class MediaListView(ListView):
    model = Media
    template_name = 'media/media_list.html'
    context_object_name = 'media_list'

@method_decorator(login_required, name='dispatch')
class MediaDetailView(DetailView):
    model = Media
    template_name = 'media/media_detail.html'
    context_object_name = 'media'

@method_decorator(login_required, name='dispatch')
class MediaCreateView(CreateView):
    model = Media
    form_class = MediaForm
    template_name = 'media/media_form.html'
    success_url = reverse_lazy('media_list')

@method_decorator(login_required, name='dispatch')
class MediaUpdateView(UpdateView):
    model = Media
    form_class = MediaForm
    template_name = 'media/media_update.html'
    success_url = reverse_lazy('media_list')

@method_decorator(login_required, name='dispatch')
class MediaDeleteView(DeleteView):
    model = Media
    template_name = 'media/media_confirm_delete.html'
    success_url = reverse_lazy('media_list')

# Gender-Specific Views
@login_required
def male_coaches_athletes(request):
    male_coaches = Coach.objects.filter(gender='Male')
    male_athletes = Athlete.objects.filter(gender='Male')
    context = {
        'coaches': male_coaches,
        'athletes': male_athletes
    }
    return render(request, 'links/male_coaches_athletes.html', context)

@login_required
def female_coaches_athletes(request):
    female_coaches = Coach.objects.filter(gender='Female')
    female_athletes = Athlete.objects.filter(gender='Female')
    context = {
        'coaches': female_coaches,
        'athletes': female_athletes
    }
    return render(request, 'links/female_coaches_athletes.html', context)

@login_required
def all_coaches_athletes(request):
    coaches = Coach.objects.all()
    athletes = Athlete.objects.all()
    context = {
        'coaches': coaches,
        'athletes': athletes
    }
    return render(request, 'links/all_coaches_athletes.html', context)

# Team Views
@method_decorator(login_required, name='dispatch')
class TeamListView(ListView):
    model = Team
    template_name = 'teams/team_list.html'
    context_object_name = 'teams'

@method_decorator(login_required, name='dispatch')
class TeamDetailView(DetailView):
    model = Team
    template_name = 'teams/team_detail.html'
    context_object_name = 'team'

@method_decorator(login_required, name='dispatch')
class TeamCreateView(CreateView):
    model = Team
    form_class = TeamForm
    template_name = 'teams/team_form.html'
    success_url = reverse_lazy('team_list')

@method_decorator(login_required, name='dispatch')
class TeamUpdateView(UpdateView):
    model = Team
    form_class = TeamForm
    template_name = 'teams/team_form.html'
    success_url = reverse_lazy('team_list')

@method_decorator(login_required, name='dispatch')
class TeamDeleteView(DeleteView):
    model = Team
    template_name = 'teams/team_confirm_delete.html'
    success_url = reverse_lazy('team_list')

# Membership Management Views
@login_required
def add_member(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == 'POST':
        form = MembershipForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            member.team = team
            member.save()
            return redirect('team_detail', pk=team.pk)
    else:
        form = MembershipForm()
    return render(request, 'team_memberships/members_form.html', {'form': form, 'team': team})
@login_required
def check_and_redirect(request):
    if Coach.objects.filter(user=request.user).exists():
        return redirect('coach_dashboard')
    # Redirect to a default page or raise an exception
    return redirect('home') 
class CoachRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if Coach.objects.filter(user=request.user).exists():
            return redirect('coach_dashboard')
        return super().dispatch(request, *args, **kwargs)
    
@login_required
def TournamentListView(request):
    if Coach.objects.filter(user=request.user).exists():
        return redirect('coach_dashboard')
    tournaments = Tournament.objects.all()
    context = {'tournaments': tournaments}
    return render(request, 'tournament/tournament_list.html', context)


class TournamentCreateView(CreateView):
    model = Tournament
    form_class = TournamentForm
    template_name = 'tournament/tournament_form.html'
    success_url = reverse_lazy('tournament_list')


class TournamentDetailsView(LoginRequiredMixin, DetailView):
    model = Tournament
    template_name = 'tournament/tournament_detail.html'
    context_object_name = 'tournament'
    pk_url_kwarg = 'tournament_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tournament = self.get_object()

        participations = TournamentParticipation.objects.filter(
            tournament=tournament
        ).select_related('athlete', 'coach', 'category')

        context.update({
            'total_participants' : TournamentParticipation.objects.filter(    tournament=tournament).values('athlete').distinct().count(),

            'total_countries': participations.values(
                'athlete__country'
            ).distinct().count(),
            'participants': participations,
            'athletes': participations.filter(athlete__isnull=False),
            'teams': participations.filter(category__name__icontains='team'),
        })

        return context
@login_required
def tournament_participants(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)

    participations = (
        TournamentParticipation.objects
        .filter(tournament=tournament)
        .select_related(
            'athlete',
            'athlete__country',
            'athlete__belt',
            'coach'
        )
        .prefetch_related('category')
    )

    athletes = participations.filter(athlete__isnull=False)
    teams = participations.filter(athlete__isnull=True)

    # Dropdowns
    countries = (
        Country.objects
        .filter(athlete_profiles__tournamentparticipation__tournament=tournament)
        .distinct()
        .order_by('name')
    )

    belts = (
        Belt.objects
        .filter(athlete_belt__tournamentparticipation__tournament=tournament)
        .distinct()
        .order_by('name')
    )

    categories = (
        Category.objects
        .filter(athlete_associations__tournamentparticipation__tournament=tournament)
        .distinct()
        .order_by('name')
    )

    return render(request, 'tournament/tournament_participants.html', {
        'tournament': tournament,
        'athletes': athletes,
        'teams': teams,
        'countries': countries,
        'belts': belts,
        'categories': categories,
    })

def generate_pdf_individual_batch(request, tournament_id):
    athlete_ids = request.GET.get('athletes', '')
    athlete_ids = [int(i) for i in athlete_ids.split(',') if i]

    tournament = Tournament.objects.get(id=tournament_id)
    athletes = Athlete.objects.filter(id__in=athlete_ids)

    # Example using ReportLab
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{tournament.name}_participants.pdf"'

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    pdf = canvas.Canvas(response, pagesize=A4)
    y = 800

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, f"{tournament.name} – Selected Athletes")
    y -= 30

    pdf.setFont("Helvetica", 12)
    for athlete in athletes:
        line = f"{athlete.name} | {athlete.country.name} | {athlete.gender} | {athlete.age} | {athlete.belt.name if athlete.belt else '—'} | {athlete.weight}"
        pdf.drawString(50, y, line)
        y -= 20
        if y < 50:  # new page if too low
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y = 800

    pdf.save()
    return response

    
class TournamentDetailsViewCoach(LoginRequiredMixin, DetailView):
    model = Tournament
    template_name = 'tournament/tournament_detail.html'
    context_object_name = 'tournament'
    pk_url_kwarg = 'tournament_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tournament = self.get_object()  # Get the Tournament object

        # Get the logged-in user
        user = self.request.user
        
        # Retrieve coach based on the user
        coach = get_coach_for_user(user.id)
        if coach:
            coach_id = coach.id
        else:
            coach_id = None

        # Calculate total participants and total countries
        total_participants = TournamentParticipation.objects.filter(tournament=tournament).count()
        total_countries = TournamentParticipation.objects.filter(tournament=tournament).values('athlete__country').distinct().count()

        # Add the data to the context
        context['total_participants'] = total_participants
        context['total_countries'] = total_countries
        context['coach_id'] = coach_id  # Add coach_id to the context if needed

        return context    
class TournamentUpdateView(UpdateView):
    model = Tournament
    form_class = TournamentForm
    template_name = 'tournament/tournament_form.html'
    success_url = reverse_lazy('tournament_list')

class TournamentDeleteView(DeleteView):
    model = Tournament
    template_name = 'tournament/tournament_confirm_delete.html'
    success_url = reverse_lazy('tournament_list')


class TournamentParticipationListView( ListView):
    model = TournamentParticipation
    template_name = 'tournament/tournament_participation_list.html'
    context_object_name = 'participations'

@login_required
def generate_pdf1(request, tournament_id, athlete_id):
    # Fetch objects
    tournament = get_object_or_404(Tournament, id=tournament_id)
    athlete = get_object_or_404(Athlete, id=athlete_id)

    participation = get_object_or_404(
        TournamentParticipation,
        tournament=tournament,
        athlete=athlete
    )

    categories = [c.name for c in participation.category.all()]
        
    # Paths
    template_path = os.path.join(
        settings.MEDIA_ROOT, 'doc',
        
        'tongil_individual_template.docx'
    )

    output_dir = os.path.join(settings.MEDIA_ROOT, 'completed_forms')
    os.makedirs(output_dir, exist_ok=True)

    docx_output = os.path.join(
        output_dir,
        f'{athlete.name}_TongIL_Registration.docx'
    )

    pdf_output = docx_output.replace('.docx', '.pdf')

    # Category checkmarks
    forms = "✔" if 'individual_form' in categories else ""
    special = "✔" if 'special_technique' in categories else ""
    sparring = "✔" if 'sparring' in categories else ""

    # Placeholder replacements
    replacements = {
        '{{family_name}}': athlete.name.split(' ')[-1] if athlete.name else '',
        '{{given_names}}': ' '.join(athlete.name.split(' ')[:-1]) if athlete.name else '',
        '{{gender}}': athlete.gender or '',
        '{{dob}}': athlete.dob.strftime('%d-%m-%Y') if athlete.dob else '',
        '{{age}}': athlete.age or '',
        '{{weight}}': athlete.weight or '',
        '{{nationality}}': athlete.country.name if athlete.country else '',
        '{{email}}': athlete.email or '',
        '{{phone}}': athlete.contacts or '',
        '{{style}}': 'Tong-IL Moo-Do',
        '{{coach_name}}': athlete.coach.name if athlete.coach else '',
        '{{rank}}': str(athlete.belt) if athlete.belt else '',
        '{{forms}}': forms,
        '{{special}}': special,
        '{{sparring}}': sparring,
        '{{full_name}}': athlete.name or '',
        '{{date}}': datetime.date.today().strftime('%d-%m-%Y'),
    }

    # Load Word template
    doc = Document(template_path)

    # Replace placeholders in paragraphs
    for paragraph in doc.paragraphs:
        for key, value in replacements.items():
            if key in paragraph.text:
                paragraph.text = paragraph.text.replace(key, str(value))

    # Replace placeholders inside tables (IMPORTANT)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for key, value in replacements.items():
                        if key in paragraph.text:
                            paragraph.text = paragraph.text.replace(key, str(value))

    # Save populated DOCX
    doc.save(docx_output)

    # Convert DOCX → PDF
    convert(docx_output, pdf_output)

    # Serve PDF
    with open(pdf_output, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="{os.path.basename(pdf_output)}"'
        )
        return response
@login_required
def generate_pdf(request, tournament_id, athlete_id):

    print(f"Starting PDF generation for tournament ID: {tournament_id} and athlete ID: {athlete_id}")

    # Fetch tournament and athlete
    tournament = get_object_or_404(Tournament, id=tournament_id)
    athlete = get_object_or_404(Athlete, id=athlete_id)

    # Fetch participation
    tp = get_object_or_404(
        TournamentParticipation,
        tournament=tournament,
        athlete=athlete
    )
    categories = [c.name for c in tp.category.all()]
    print(f"Fetched TournamentParticipation ID={tp.id} with categories: {categories}")

    # PDF paths
    pdf_template_path = os.path.join(
        settings.MEDIA_ROOT, 'doc', 'tongil_individual2025.pdf'
    )
    pdf_output_dir = os.path.join(settings.MEDIA_ROOT, 'completed_forms')
    os.makedirs(pdf_output_dir, exist_ok=True)

    pdf_output_path = os.path.join(
        pdf_output_dir,
        f'{athlete.name}_{tournament.edition}th_Edition_Consent_Form.pdf'
    )

    # Category → checkbox mapping (must match PDFescape field names)
    category_map = {
        'individual_form': 'CheckBox1',
        'special_technique': 'CheckBox2',
        'sparring': 'CheckBox3',
    }

    # Set checkbox values
    category_checks = {category_map[c]: 'Yes' for c in categories if c in category_map}
    for key in category_map.values():
        category_checks.setdefault(key, 'No')

    # Athlete data → PDF fields
    athlete_data = {
        'Text1': athlete.name.split(' ')[-1] if athlete.name else '',
        'Text2': ' '.join(athlete.name.split(' ')[:-1]) if athlete.name else '',
        'Text3': athlete.gender or '',
        'Text4': athlete.dob.strftime('%d-%m-%Y') if athlete.dob else '',
        'Text5': athlete.age or '',
        'Text6': str(athlete.weight) if athlete.weight else '',
        'Text7': athlete.country.name if athlete.country else '',
        #'Text8': athlete.address or '',
        'Text9': athlete.email or '',
        'Text10': athlete.contacts or '',
        'Text11': str(athlete.belt) if athlete.belt else '',
        'Text12': athlete.coach.name if athlete.coach else '',
        'Text13': str(athlete.coach.belt) if athlete.coach and athlete.coach.belt else '',
        'Text14': athlete.name or '',
        'Text15': '',  # Signature
        'Text16': datetime.datetime.today().strftime('%d-%m-%Y'),
    }

    # Merge checkbox values
    athlete_data.update(category_checks)

    # Filter only existing PDF fields
    form_fields = fillpdfs.get_form_fields(pdf_template_path)
    filtered_data = {k: v for k, v in athlete_data.items() if k in form_fields}

    try:
        # 1️⃣ Fill the PDF
        fillpdfs.write_fillable_pdf(
        input_pdf_path=pdf_template_path,
        output_pdf_path=pdf_output_path,
        data_dict=filtered_data
)

        # THIS is what makes fields "transparent"
        fillpdfs.flatten_pdf(pdf_output_path, pdf_output_path)


        print(f"PDF successfully generated and flattened: {pdf_output_path}")

        # Return PDF
        with open(pdf_output_path, 'rb') as pdf_file:
            response = HttpResponse(
                pdf_file.read(),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = (
                f'attachment; filename="{os.path.basename(pdf_output_path)}"'
            )
            return response

    except Exception as e:
        print(f"Error generating PDF for athlete {athlete.id}: {e}")
        return HttpResponse("Error generating PDF", status=500)
    
class TournamentParticipationCreateView(CreateView):
    model = TournamentParticipation
    form_class = TournamentParticipationForm
    template_name = 'tournament/tournament_participation_form.html'
    success_url = reverse_lazy('tournament_participation_list')

class TournamentParticipationUpdateView(UpdateView):
    model = TournamentParticipation
    form_class = TournamentParticipationForm
    template_name = 'tournament/tournament_participation_form.html'
    success_url = reverse_lazy('tournament_participation_list')

class TournamentParticipationDeleteView(DeleteView):
    model = TournamentParticipation
    template_name = 'tournament/tournament_participation_confirm_delete.html'
    success_url = reverse_lazy('tournament_participation_list')
def results_list(request):
    results = TournamentResult.objects.all().order_by('tournament', 'category', 'rank')

    tournament_id = request.GET.get('tournament')
    category_id = request.GET.get('category')
    athlete_id = request.GET.get('athlete')
    coach_id = request.GET.get('coach')

    if tournament_id:
        results = results.filter(tournament_id=tournament_id)
    if category_id:
        results = results.filter(category_id=category_id)
    if athlete_id:
        results = results.filter(athlete_id=athlete_id)
    if coach_id:
        results = results.filter(coach_id=coach_id)

    tournaments = Tournament.objects.all()
    categories = Category.objects.all()
    athletes = Athlete.objects.all()
    coaches = Coach.objects.all()

    return render(request, 'results/results_list.html', {
        'results': results,
        'tournaments': tournaments,
        'categories': categories,
        'athletes': athletes,
        'coaches': coaches
    })


# Batch PDF Export
def results_batch_pdf(request):
    ids = request.GET.getlist('ids[]')  # List of result IDs
    results = TournamentResult.objects.filter(id__in=ids).order_by('tournament', 'category', 'rank')

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=(595, 842))  # A4

    y = 800
    for r in results:
        participant = r.athlete.name if r.athlete else r.coach.name
        line = f"{r.tournament.name} | {participant} | {r.category.name} | Rank: {r.rank} | Score: {r.score} | Medal: {r.medal or ''}"
        p.drawString(30, y, line)
        y -= 20
        if y < 50:
            p.showPage()
            y = 800

    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')
# Create
def results_create(request):
    if request.method == 'POST':
        form = TournamentResultForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('results_list')
    else:
        form = TournamentResultForm()
    return render(request, 'results/results_form.html', {'form': form, 'title': 'Add Result'})

# Update
def results_update(request, pk):
    result = get_object_or_404(TournamentResult, pk=pk)
    if request.method == 'POST':
        form = TournamentResultForm(request.POST, instance=result)
        if form.is_valid():
            form.save()
            return redirect('results_list')
    else:
        form = TournamentResultForm(instance=result)
    return render(request, 'results/results_form.html', {'form': form, 'title': 'Edit Result'})

# Delete
def results_delete(request, pk):
    result = get_object_or_404(TournamentResult, pk=pk)
    if request.method == 'POST':
        result.delete()
        return redirect('results_list')
    return render(request, 'results/results_confirm_delete.html', {'result': result})

def generate_pdf_selected(request, tournament_id):
    athlete_ids = request.POST.getlist('athlete_ids')

    if not athlete_ids:
        messages.error(request, "No athletes selected.")
        return redirect(request.META.get('HTTP_REFERER'))

    participations = TournamentParticipation.objects.filter(
        tournament_id=tournament_id,
        athlete_id__in=athlete_ids
    )

    # generate consent form PDFs
    # zip them OR merge into one PDF


from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django.http import HttpResponse
from .models import TournamentResult
from collections import defaultdict

def results_batch_pdf_grouped(request):
    ids = request.GET.getlist('ids[]')
    results = TournamentResult.objects.filter(id__in=ids).order_by('tournament', 'category', 'rank')

    # Group by tournament then category
    grouped = defaultdict(lambda: defaultdict(list))
    for r in results:
        grouped[r.tournament][r.category].append(r)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    styleH = styles['Heading2']
    styleN = styles['Normal']

    for tournament, categories in grouped.items():
        elements.append(Paragraph(f"{tournament.name} – {tournament.edition} Edition", styleH))
        elements.append(Spacer(1, 12))
        for category, res_list in categories.items():
            elements.append(Paragraph(f"Category: {category.name}", styles['Heading3']))
            data = [['#', 'Participant', 'Rank', 'Score', 'Medal']]
            for idx, r in enumerate(res_list, 1):
                participant = r.athlete.name if r.athlete else r.coach.name
                data.append([idx, participant, r.rank, r.score, r.medal or ''])
            t = Table(data, repeatRows=1)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#d9d9d9')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('ALIGN',(0,0),(-1,-1),'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 20))

        elements.append(Spacer(1, 30))

    doc.build(elements)
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

# Authentication Views
class CustomLoginView(LoginView):
    template_name = 'login.html'

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')



