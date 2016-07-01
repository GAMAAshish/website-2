from hashlib import md5

from cms.models.pluginmodel import CMSPlugin
from cms.extensions import PageExtension
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.text import slugify
from django_countries.fields import CountryField
from geoposition.fields import GeopositionField


class Person(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=100)
    username_on_slack = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True)
    photo = models.ImageField(upload_to='organisation/people/photos',
                              blank=True)
    twitter = models.CharField(max_length=18, blank=True)
    url = models.URLField(blank=True)

    def __unicode__(self):
        return self.name

    @property
    def gravatar_url(self):
        """ Returns the gravatar url for this user (constructed from email)"""
        base = "https://gravatar.com/avatar/{hash}/"
        md5_hash = md5(self.email.strip().lower()).hexdigest()
        return base.format(hash=md5_hash)

    @property
    def nowdoing_with_latest(self):
        """ All NowDoing attributes of the user with the most recently
            updated one marked with `is_newest_update`"""
        nowdoings = self.nowdoing_set.all().extra(order_by=['-updated_at'])
        if nowdoings:
            nowdoings[0].is_newest_update = True
        return nowdoings

    @property
    def has_anything_to_show(self):
        """ Is there anything that we can show for this person in the
            template (other then email which is checked separately)"""
        return (self.url or
                self.twitter or
                self.nowdoing_set.count())

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "people"


class NowDoing(models.Model):
    ACTIVITIES = (
        ('reading', 'reading'),
        ('listening', 'listening'),
        ('working', 'working'),
        ('location', 'location'),
        ('watching', 'watching'),
        ('eating', 'eating'),
        )
    person = models.ForeignKey(Person)
    doing_type = models.CharField(
        max_length=10,
        choices=ACTIVITIES)
    link = models.URLField(blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def icon_name(self):
        """ The name of the corresponding css icon class """
        matching = {'watching': 'playing'}
        return matching.get(self.doing_type, self.doing_type)

    @property
    def display_name(self):
        """ The human readable string to be displayed in templates """
        matching = {
            'reading': 'Reading',
            'listening': 'Listening to',
            'working': 'Working on',
            'location': 'Location',
            'watching': 'Watching',
            'eating': 'Eating'
            }
        return matching.get(self.doing_type, self.doing_type)

    def __repr__(self):
        return '<NowDoing: {}, {}>'.format(self.person.name,
                                           self.doing_type)


class Unit(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=100)
    members = models.ManyToManyField('Person', through='UnitMembership')
    order = models.IntegerField(
        blank=True, null=True,
        help_text="Higher numbers mean higher up in the food chain")

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["-order", "name"]


class UnitMembership(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=100)
    person = models.ForeignKey('Person')
    unit = models.ForeignKey('Unit')
    order = models.IntegerField(
        blank=True, null=True,
        help_text="Higher numbers mean higher up in the food chain")

    def __unicode__(self):
        return self.person.name + ' - ' + self.title

    class Meta:
        ordering = ["-order", "person__name"]


class Board(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    members = models.ManyToManyField('Person', through='BoardMembership')

    def __unicode__(self):
        return self.name


class BoardMembership(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=100)
    person = models.ForeignKey('Person')
    board = models.ForeignKey('Board')

    def __unicode__(self):
        return self.person.name + ' - ' + self.title


class Project(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    teaser = models.CharField(
        max_length=100,
        help_text="A single line description for list views")
    description = models.TextField()
    banner = models.ImageField(
        upload_to='projects/banners',
        blank=True,
        help_text="A banner used for featuring this project on the front page")
    picture = models.ImageField(
        upload_to='projects/pictures',
        blank=True,
        help_text="A simple logo or picture to represent this project")

    twitter = models.CharField(max_length=18, blank=True)
    homepage_url = models.URLField(blank=True)
    sourcecode_url = models.URLField(blank=True)
    mailinglist_url = models.URLField(blank=True)

    featured = models.BooleanField(
        default=False,
        help_text="Should this be a featured project?")
    themes = models.ManyToManyField('Theme', blank=True)
    types = models.ManyToManyField('ProjectType', blank=True)

    def get_absolute_url(self):
        return reverse('project', kwargs={'slug': self.slug})

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class ProjectType(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    def __unicode__(self):
        return self.name


class Theme(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    blurb = models.TextField(help_text='Blurb for theme page')
    description = models.TextField()
    picture = models.ImageField(
        upload_to='themes/pictures',
        blank=True,
        help_text="A simple logo or picture to represent this theme")

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('theme', kwargs={'slug': self.slug})


class WorkingGroupManager(models.Manager):

    def active(self):
        return self.get_queryset().filter(incubation=False)

    def incubators(self):
        return self.get_queryset().filter(incubation=True)


class WorkingGroup(models.Model):
    objects = WorkingGroupManager()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    description = models.TextField()
    homepage_url = models.URLField(blank=True)
    logo = models.ImageField(upload_to='organisation/working-groups/logos',
                             blank=True)

    incubation = models.BooleanField(default=True,
                                     help_text='Is this group in incubation?')

    themes = models.ManyToManyField('Theme', blank=True,
                                    related_name='workinggroups')

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class NetworkGroupManager(models.Manager):

    def countries(self):
        return self.get_queryset().filter(region_slug='')

    def regions(self, country):
        return self.get_queryset().exclude(region_slug='')\
            .filter(country_slug=country)


class NetworkGroup(models.Model):
    objects = NetworkGroupManager()

    GROUP_TYPES = ((0, 'Local group'),
                   (1, 'Chapter'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=100)

    group_type = models.IntegerField(default=0, choices=GROUP_TYPES)
    description = models.TextField(blank=True, null=True)

    country = CountryField()
    country_slug = models.SlugField()
    region = models.CharField(max_length=100, blank=True)
    region_slug = models.SlugField(default=None)

    mailinglist_url = models.URLField(blank=True)
    homepage_url = models.URLField(blank=True)
    twitter = models.CharField(max_length=18, blank=True)
    facebook_url = models.URLField(blank=True)

    position = GeopositionField(blank=True, null=True)

    extra_information = models.TextField(blank=True, null=True)

    members = models.ManyToManyField('Person',
                                     through='NetworkGroupMembership')
    working_groups = models.ManyToManyField('WorkingGroup', blank=True)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.twitter and self.twitter.startswith(u'@'):
            self.twitter = self.twitter[1:]

        # Slug is either the country slugified or the region
        # Therefore we cannot force slug to be unique
        # (regions might have same name in different countries)
        self.country_slug = slugify(self.get_country_display())
        self.region_slug = slugify(self.region)

        super(NetworkGroup, self).save(*args, **kwargs)

    def get_absolute_url(self):
        # Because reverse can't be smart about conditional parameters
        # we have to have two different urls depending on if it is a
        # country or a region group
        if self.region:
            return reverse('network-region',
                           kwargs={'country': self.country_slug,
                                   'region': self.region_slug})
        else:
            return reverse('network-country',
                           kwargs={'country': self.country_slug})

    class Meta:
        unique_together = ('country', 'region')
        ordering = ('country', 'region')


class NetworkGroupMembership(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=100, blank=True)
    order = models.IntegerField(
        blank=True, null=True,
        help_text="The lower the number the higher on the"
        " page this Person will be shown.")
    networkgroup = models.ForeignKey('NetworkGroup')
    person = models.ForeignKey('Person')

    def __unicode__(self):
        return self.person.name + ' - ' + self.networkgroup.name

    class Meta:
        ordering = ["-order", "person__name"]


class FeaturedTheme(CMSPlugin):
    theme = models.ForeignKey('Theme', related_name='+')

    def __unicode__(self):
        return self.theme.name


class FeaturedProject(CMSPlugin):
    project = models.ForeignKey('Project', related_name='+')

    def __unicode__(self):
        return self.project.name


class NetworkGroupList(CMSPlugin):
    group_type = models.IntegerField(default=0,
                                     choices=NetworkGroup.GROUP_TYPES)

    def __unicode__(self):
        return self.get_group_type_display()


class ProjectList(CMSPlugin):
    theme = models.ForeignKey(
        'Theme', blank=True, null=True,
        help_text='Limit to projects with this theme')
    project_type = models.ForeignKey(
        'ProjectType', blank=True, null=True,
        help_text='Limit to projects with this type')


class SignupForm(CMSPlugin):
    title = models.CharField(max_length=50,
                             default='Get Connected to Open Knowledge')
    description = models.TextField(blank=True)


class SideBarExtension(PageExtension):
    enabled = models.BooleanField(default=True)
