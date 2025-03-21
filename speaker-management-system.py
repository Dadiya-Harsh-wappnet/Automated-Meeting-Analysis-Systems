import datetime
import csv
import os
from typing import List, Dict, Optional, Tuple
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd
import joblib
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class Speaker:
    def __init__(self, id: str, name: str, email: str, phone: str, 
                 organization: str = "", specialization: str = "", bio: str = "", 
                 rating: float = None, past_events: int = 0):
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
        self.organization = organization
        self.specialization = specialization
        self.bio = bio
        self.rating = rating  # Speaker rating (1-5)
        self.past_events = past_events  # Number of past events speaker has participated in
        self.transportation_needs = []
        self.meetings = []
        self.availability = []  # List of available time slots
        self.preferences = {}  # Preferences like hotel, meal, etc.
        self.embedding = None  # For storing speaker vector representation
    
    def add_transportation_need(self, transport_type: str, pickup_location: str, 
                                destination: str, datetime_needed: datetime.datetime,
                                special_requirements: str = "", priority: int = 2):
        """Add transportation requirement for this speaker"""
        transport = {
            "type": transport_type,
            "pickup": pickup_location,
            "destination": destination,
            "datetime": datetime_needed,
            "special_requirements": special_requirements,
            "status": "Pending",
            "priority": priority,  # 1 (high) to 3 (low)
            "coordinates": {"pickup": None, "destination": None}  # For geo-coordinates
        }
        self.transportation_needs.append(transport)
        return len(self.transportation_needs) - 1  # Return index of added transport
    
    def update_transport_status(self, transport_index: int, new_status: str):
        """Update status of a transportation request"""
        if 0 <= transport_index < len(self.transportation_needs):
            self.transportation_needs[transport_index]["status"] = new_status
            return True
        return False
    
    def assign_to_meeting(self, meeting_id: str, role: str = "Speaker"):
        """Assign speaker to a meeting"""
        self.meetings.append({"meeting_id": meeting_id, "role": role})
    
    def add_availability(self, start_time: datetime.datetime, end_time: datetime.datetime):
        """Add time slot when speaker is available"""
        self.availability.append({"start": start_time, "end": end_time})
    
    def add_preference(self, preference_type: str, value: str):
        """Add speaker preference"""
        self.preferences[preference_type] = value


class Meeting:
    def __init__(self, id: str, title: str, date: datetime.datetime, 
                 location: str, duration_minutes: int = 60, max_speakers: int = None,
                 topic_keywords: List[str] = None, importance: int = 2):
        self.id = id
        self.title = title
        self.date = date
        self.location = location
        self.duration_minutes = duration_minutes
        self.max_speakers = max_speakers
        self.speakers = []  # List of speaker IDs and roles
        self.notes = ""
        self.topic_keywords = topic_keywords or []
        self.importance = importance  # 1 (critical) to 3 (regular)
        self.coordinates = None  # Geo-coordinates
    
    def add_speaker(self, speaker_id: str, role: str = "Speaker"):
        """Add a speaker to this meeting"""
        if self.max_speakers and len(self.speakers) >= self.max_speakers:
            return False
        self.speakers.append({"speaker_id": speaker_id, "role": role})
        return True
    
    def remove_speaker(self, speaker_id: str):
        """Remove a speaker from this meeting"""
        self.speakers = [s for s in self.speakers if s["speaker_id"] != speaker_id]
    
    def get_speaker_count(self):
        """Get the current number of speakers"""
        return len(self.speakers)


class TransportationProvider:
    def __init__(self, id: int, name: str, contact: str, transport_types: List[str], 
                 max_capacity: int, cost_per_km: float, base_cost: float = 0,
                 reliability_score: float = None, availability: List[Dict] = None):
        self.id = id
        self.name = name
        self.contact = contact
        self.transport_types = transport_types
        self.max_capacity = max_capacity
        self.cost_per_km = cost_per_km
        self.base_cost = base_cost
        self.reliability_score = reliability_score or 3.0  # 1-5 rating
        self.availability = availability or []  # List of available time slots
        self.current_assignments = []  # Current transportation assignments
    
    def add_availability(self, start_time: datetime.datetime, end_time: datetime.datetime):
        """Add time slot when provider is available"""
        self.availability.append({"start": start_time, "end": end_time})
    
    def check_availability(self, required_time: datetime.datetime, duration_minutes: int = 60):
        """Check if provider is available at the specified time"""
        for slot in self.availability:
            if (slot["start"] <= required_time and 
                required_time + datetime.timedelta(minutes=duration_minutes) <= slot["end"]):
                return True
        return False
    
    def estimate_cost(self, distance_km: float):
        """Estimate transportation cost based on distance"""
        return self.base_cost + (distance_km * self.cost_per_km)
    
    def assign_transport(self, speaker_id: str, transport_details: Dict):
        """Assign a transportation task to this provider"""
        assignment = {
            "speaker_id": speaker_id,
            "details": transport_details,
            "assigned_time": datetime.datetime.now()
        }
        self.current_assignments.append(assignment)
        return len(self.current_assignments) - 1
    
    def calculate_capacity_utilization(self):
        """Calculate current capacity utilization percentage"""
        return (len(self.current_assignments) / self.max_capacity) * 100 if self.max_capacity > 0 else 100


class SpeakerManagementSystem:
    def __init__(self):
        self.speakers = {}  # Dictionary of Speaker objects with ID as key
        self.meetings = {}  # Dictionary of Meeting objects with ID as key
        self.transportation_providers = []  # List of TransportationProvider objects
        self.geolocator = Nominatim(user_agent="speaker_management_system")
        self.speaker_clusters = None  # For storing speaker clustering model
        self.transport_predictor = None  # For predicting optimal transportation
        self.speaker_vectorizer = None  # For converting speaker info to vectors
    
    def add_speaker(self, speaker: Speaker):
        """Add a new speaker to the system"""
        self.speakers[speaker.id] = speaker
        return speaker.id
    
    def add_meeting(self, meeting: Meeting):
        """Add a new meeting to the system"""
        self.meetings[meeting.id] = meeting
        return meeting.id
    
    def get_speakers_by_meeting(self, meeting_id: str) -> List[Speaker]:
        """Get all speakers assigned to a specific meeting"""
        if meeting_id not in self.meetings:
            return []
        
        meeting_speakers = []
        for speaker_info in self.meetings[meeting_id].speakers:
            speaker_id = speaker_info["speaker_id"]
            if speaker_id in self.speakers:
                meeting_speakers.append(self.speakers[speaker_id])
        
        return meeting_speakers
    
    def get_meetings_by_speaker(self, speaker_id: str) -> List[Meeting]:
        """Get all meetings a speaker is assigned to"""
        if speaker_id not in self.speakers:
            return []
        
        speaker_meetings = []
        for meeting_info in self.speakers[speaker_id].meetings:
            meeting_id = meeting_info["meeting_id"]
            if meeting_id in self.meetings:
                speaker_meetings.append(self.meetings[meeting_id])
        
        return speaker_meetings
    
    def add_transportation_provider(self, name: str, contact: str, 
                                   transport_types: List[str], max_capacity: int, 
                                   cost_per_km: float, base_cost: float = 0,
                                   reliability_score: float = None):
        """Add a transportation provider to the system"""
        provider_id = len(self.transportation_providers) + 1
        provider = TransportationProvider(
            provider_id, name, contact, transport_types, 
            max_capacity, cost_per_km, base_cost, reliability_score
        )
        self.transportation_providers.append(provider)
        return provider_id
    
    def assign_transportation(self, speaker_id: str, transport_index: int, provider_id: int):
        """Assign a transportation provider to a speaker's transportation need"""
        if (speaker_id in self.speakers and 
            0 <= transport_index < len(self.speakers[speaker_id].transportation_needs) and
            1 <= provider_id <= len(self.transportation_providers)):
            
            speaker = self.speakers[speaker_id]
            transport = speaker.transportation_needs[transport_index]
            provider = self.transportation_providers[provider_id-1]
            
            # Check provider availability
            if not provider.check_availability(transport["datetime"]):
                return False, "Provider not available at requested time"
            
            # Assign transportation
            transport["provider_id"] = provider_id
            transport["status"] = "Assigned"
            
            # Add to provider's assignments
            provider.assign_transport(speaker_id, transport)
            
            return True, "Transportation assigned successfully"
        return False, "Invalid parameters for transportation assignment"
    
    def get_coordinates(self, address: str):
        """Get geo-coordinates for an address"""
        try:
            location = self.geolocator.geocode(address)
            if location:
                return (location.latitude, location.longitude)
        except:
            pass
        return None
    
    def calculate_distance(self, coord1, coord2):
        """Calculate distance between two coordinates in km"""
        if coord1 and coord2:
            return geodesic(coord1, coord2).kilometers
        return None
    
    def update_coordinates(self):
        """Update geo-coordinates for all addresses in the system"""
        # Update meeting locations
        for meeting_id, meeting in self.meetings.items():
            if not meeting.coordinates:
                meeting.coordinates = self.get_coordinates(meeting.location)
        
        # Update transportation pickup/destination
        for speaker_id, speaker in self.speakers.items():
            for transport in speaker.transportation_needs:
                if not transport["coordinates"]["pickup"]:
                    transport["coordinates"]["pickup"] = self.get_coordinates(transport["pickup"])
                if not transport["coordinates"]["destination"]:
                    transport["coordinates"]["destination"] = self.get_coordinates(transport["destination"])
    
    def cluster_speakers(self, n_clusters=3):
        """Group speakers into clusters based on their characteristics"""
        # Prepare data for clustering
        speaker_data = []
        speaker_ids = []
        
        for speaker_id, speaker in self.speakers.items():
            features = [
                speaker.past_events,
                speaker.rating if speaker.rating else 0,
                len(speaker.meetings),
                len(speaker.transportation_needs)
            ]
            speaker_data.append(features)
            speaker_ids.append(speaker_id)
        
        if not speaker_data:
            return {}
        
        # Standardize features
        X = np.array(speaker_data)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Apply KMeans clustering
        kmeans = KMeans(n_clusters=min(n_clusters, len(speaker_data)), random_state=42)
        clusters = kmeans.fit_predict(X_scaled)
        
        # Store model for future use
        self.speaker_clusters = {
            'model': kmeans,
            'scaler': scaler,
            'features': ['past_events', 'rating', 'meeting_count', 'transport_count']
        }
        
        # Group speakers by cluster
        speaker_groups = {}
        for i, cluster_id in enumerate(clusters):
            cluster_name = f"Cluster {cluster_id + 1}"
            if cluster_name not in speaker_groups:
                speaker_groups[cluster_name] = []
            speaker_groups[cluster_name].append(speaker_ids[i])
        
        return speaker_groups
    
    def analyze_speaker_clusters(self):
        """Analyze characteristics of each speaker cluster"""
        if not self.speaker_clusters:
            self.cluster_speakers()
        
        speaker_groups = self.cluster_speakers()
        cluster_analysis = {}
        
        for cluster_name, speaker_ids in speaker_groups.items():
            cluster_stats = {
                'count': len(speaker_ids),
                'avg_rating': 0,
                'avg_past_events': 0,
                'common_specializations': [],
                'speaker_examples': speaker_ids[:3]  # First 3 examples
            }
            
            # Collect specializations
            specializations = {}
            total_rating = 0
            total_past_events = 0
            count_with_rating = 0
            
            for speaker_id in speaker_ids:
                speaker = self.speakers[speaker_id]
                
                if speaker.specialization:
                    if speaker.specialization not in specializations:
                        specializations[speaker.specialization] = 0
                    specializations[speaker.specialization] += 1
                
                if speaker.rating:
                    total_rating += speaker.rating
                    count_with_rating += 1
                
                total_past_events += speaker.past_events
            
            # Calculate averages
            if count_with_rating > 0:
                cluster_stats['avg_rating'] = total_rating / count_with_rating
            
            if speaker_ids:
                cluster_stats['avg_past_events'] = total_past_events / len(speaker_ids)
            
            # Get top specializations
            top_specializations = sorted(specializations.items(), key=lambda x: x[1], reverse=True)
            cluster_stats['common_specializations'] = [s[0] for s in top_specializations[:3]]
            
            cluster_analysis[cluster_name] = cluster_stats
        
        return cluster_analysis
    
    def train_transportation_predictor(self):
        """Train a model to predict transportation cost and efficiency"""
        # Collect data for training
        train_data = []
        
        for speaker_id, speaker in self.speakers.items():
            for transport in speaker.transportation_needs:
                if ("provider_id" in transport and 
                    transport["coordinates"]["pickup"] and 
                    transport["coordinates"]["destination"]):
                    
                    provider = self.transportation_providers[transport["provider_id"]-1]
                    distance = self.calculate_distance(
                        transport["coordinates"]["pickup"],
                        transport["coordinates"]["destination"]
                    )
                    
                    if distance:
                        features = [
                            distance,
                            provider.max_capacity,
                            provider.reliability_score,
                            transport["priority"]
                        ]
                        cost = provider.estimate_cost(distance)
                        
                        train_data.append(features + [cost])
        
        if len(train_data) < 5:  # Need sufficient data for training
            return False
        
        # Train a linear regression model
        X = np.array([row[:-1] for row in train_data])
        y = np.array([row[-1] for row in train_data])
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Store model
        self.transport_predictor = {
            'model': model,
            'features': ['distance', 'capacity', 'reliability', 'priority']
        }
        
        return True
    
    def recommend_transportation_provider(self, speaker_id: str, transport_index: int):
        """Recommend the best transportation provider for a specific need"""
        if (speaker_id not in self.speakers or 
            transport_index >= len(self.speakers[speaker_id].transportation_needs)):
            return None, "Invalid speaker or transport index"
        
        transport = self.speakers[speaker_id].transportation_needs[transport_index]
        
        # Ensure coordinates are available
        if not transport["coordinates"]["pickup"] or not transport["coordinates"]["destination"]:
            pickup_coords = self.get_coordinates(transport["pickup"])
            dest_coords = self.get_coordinates(transport["destination"])
            
            if pickup_coords:
                transport["coordinates"]["pickup"] = pickup_coords
            if dest_coords:
                transport["coordinates"]["destination"] = dest_coords
        
        if not transport["coordinates"]["pickup"] or not transport["coordinates"]["destination"]:
            return None, "Could not determine coordinates for transportation"
        
        # Calculate distance
        distance = self.calculate_distance(
            transport["coordinates"]["pickup"],
            transport["coordinates"]["destination"]
        )
        
        if not distance:
            return None, "Could not calculate distance"
        
        # Find available providers that match the transport type
        available_providers = []
        for provider in self.transportation_providers:
            if (transport["type"] in provider.transport_types and 
                provider.check_availability(transport["datetime"])):
                
                # Calculate score: 70% cost, 20% reliability, 10% capacity utilization
                if self.transport_predictor:
                    # Use trained model if available
                    X = np.array([[
                        distance, 
                        provider.max_capacity,
                        provider.reliability_score,
                        transport["priority"]
                    ]])
                    predicted_cost = self.transport_predictor['model'].predict(X)[0]
                else:
                    # Otherwise use provider's cost formula
                    predicted_cost = provider.estimate_cost(distance)
                
                utilization = provider.calculate_capacity_utilization()
                
                # Calculate score (lower is better)
                cost_score = predicted_cost / 100  # Normalize cost
                reliability_score = (5 - provider.reliability_score) / 4  # Invert so lower is better
                utilization_score = utilization / 100
                
                total_score = (0.7 * cost_score + 
                              0.2 * reliability_score + 
                              0.1 * utilization_score)
                
                available_providers.append({
                    'provider': provider,
                    'score': total_score,
                    'cost': predicted_cost,
                    'distance': distance
                })
        
        if not available_providers:
            return None, "No available providers match requirements"
        
        # Sort by score (lower is better)
        available_providers.sort(key=lambda x: x['score'])
        best_provider = available_providers[0]['provider']
        
        return best_provider, {
            'estimated_cost': available_providers[0]['cost'],
            'distance_km': distance,
            'score': available_providers[0]['score'],
            'alternatives': len(available_providers) - 1
        }
    
    def vectorize_speakers(self):
        """Create vector representations of speakers based on their text data"""
        # Combine relevant text data for each speaker
        speaker_texts = {}
        for speaker_id, speaker in self.speakers.items():
            text = f"{speaker.name} {speaker.organization} {speaker.specialization} {speaker.bio}"
            speaker_texts[speaker_id] = text
        
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
        text_data = list(speaker_texts.values())
        
        if not text_data:
            return False
        
        # Fit and transform text data
        speaker_vectors = vectorizer.fit_transform(text_data)
        
        # Store vectorizer and speaker vectors
        self.speaker_vectorizer = vectorizer
        
        # Assign embeddings to speakers
        for i, (speaker_id, _) in enumerate(speaker_texts.items()):
            self.speakers[speaker_id].embedding = speaker_vectors[i].toarray()[0]
        
        return True
    
    def find_similar_speakers(self, speaker_id: str, top_n=3):
        """Find speakers most similar to the given speaker"""
        if speaker_id not in self.speakers:
            return []
        
        # Ensure speakers have embeddings
        if not self.speaker_vectorizer:
            self.vectorize_speakers()
        
        # Check if speaker has embedding
        if self.speakers[speaker_id].embedding is None:
            return []
        
        # Calculate similarity between target speaker and all others
        similarities = []
        target_embedding = self.speakers[speaker_id].embedding
        
        for other_id, other_speaker in self.speakers.items():
            if other_id != speaker_id and other_speaker.embedding is not None:
                similarity = cosine_similarity(
                    [target_embedding], 
                    [other_speaker.embedding]
                )[0][0]
                
                similarities.append((other_id, similarity))
        
        # Sort by similarity (higher is more similar)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N similar speakers
        similar_speakers = []
        for other_id, similarity in similarities[:top_n]:
            similar_speakers.append({
                'speaker': self.speakers[other_id],
                'similarity_score': similarity
            })
        
        return similar_speakers
    
    def recommend_speakers_for_meeting(self, meeting_id: str, top_n=5):
        """Recommend speakers for a specific meeting based on topic relevance"""
        if meeting_id not in self.meetings:
            return []
        
        meeting = self.meetings[meeting_id]
        
        # Ensure speakers have embeddings
        if not self.speaker_vectorizer:
            self.vectorize_speakers()
        
        # If meeting has no keywords, can't make recommendations
        if not meeting.topic_keywords:
            return []
        
        # Create a text representation of the meeting
        meeting_text = f"{meeting.title} {' '.join(meeting.topic_keywords)}"
        
        # Vectorize the meeting text
        meeting_vector = self.speaker_vectorizer.transform([meeting_text]).toarray()[0]
        
        # Calculate relevance score for each speaker
        relevance_scores = []
        
        for speaker_id, speaker in self.speakers.items():
            # Skip speakers already assigned to this meeting
            if any(s['meeting_id'] == meeting_id for s in speaker.meetings):
                continue
            
            # Skip speakers without embeddings
            if speaker.embedding is None:
                continue
            
            # Calculate relevance score
            relevance = cosine_similarity([meeting_vector], [speaker.embedding])[0][0]
            
            # Include speaker rating as a factor
            rating_factor = speaker.rating / 5 if speaker.rating else 0.5
            
            # Include experience as a factor
            experience_factor = min(1, speaker.past_events / 10)
            
            # Combined score: 60% relevance, 25% rating, 15% experience
            combined_score = (0.6 * relevance + 
                             0.25 * rating_factor + 
                             0.15 * experience_factor)
            
            relevance_scores.append({
                'speaker': speaker,
                'relevance_score': relevance,
                'combined_score': combined_score
            })
        
        # Sort by combined score
        relevance_scores.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return relevance_scores[:top_n]
    
    def optimize_transportation_schedule(self):
        """Optimize transportation schedule to minimize cost and maximize efficiency"""
        # Group transportation needs by date and nearby locations
        transport_groups = {}
        
        # First, ensure coordinates are updated
        self.update_coordinates()
        
        # Group by date (rounded to hour)
        for speaker_id, speaker in self.speakers.items():
            for i, transport in enumerate(speaker.transportation_needs):
                if transport["status"] == "Pending":
                    # Round datetime to nearest hour
                    hour_key = transport["datetime"].replace(minute=0, second=0, microsecond=0)
                    date_key = hour_key.strftime("%Y-%m-%d %H:00")
                    
                    if date_key not in transport_groups:
                        transport_groups[date_key] = []
                    
                    transport_groups[date_key].append({
                        'speaker_id': speaker_id,
                        'transport_index': i,
                        'transport': transport
                    })
        
        # Process each group
        optimized_assignments = []
        
        for date_key, transports in transport_groups.items():
            # Skip groups with only one transportation need
            if len(transports) <= 1:
                continue
            
            # Check if locations are close enough to share transportation
            for i in range(len(transports)):
                for j in range(i+1, len(transports)):
                    t1 = transports[i]['transport']
                    t2 = transports[j]['transport']
                    
                    # Check if pickup locations are close
                    if (t1["coordinates"]["pickup"] and t2["coordinates"]["pickup"]):
                        pickup_distance = self.calculate_distance(
                            t1["coordinates"]["pickup"],
                            t2["coordinates"]["pickup"]
                        )
                        
                        # Check if destinations are close
                        if (t1["coordinates"]["destination"] and t2["coordinates"]["destination"]):
                            dest_distance = self.calculate_distance(
                                t1["coordinates"]["destination"],
                                t2["coordinates"]["destination"]
                            )
                            
                            # If both pickup and destinations are within 3km, can share
                            if pickup_distance and dest_distance and pickup_distance <= 3 and dest_distance <= 3:
                                # Find a provider with enough capacity
                                for provider in self.transportation_providers:
                                    # Need capacity for at least 2 people
                                    if (provider.max_capacity >= 2 and 
                                        t1["type"] in provider.transport_types and
                                        provider.check_availability(t1["datetime"])):
                                        
                                        # Create a shared transportation assignment
                                        shared_assignment = {
                                            'provider': provider,
                                            'datetime': t1["datetime"],
                                            'transports': [
                                                {
                                                    'speaker_id': transports[i]['speaker_id'],
                                                    'transport_index': transports[i]['transport_index']
                                                },
                                                {
                                                    'speaker_id': transports[j]['speaker_id'],
                                                    'transport_index': transports[j]['transport_index']
                                                }
                                            ],
                                            'pickup_area': 'Area around ' + t1["pickup"],
                                            'destination_area': 'Area around ' + t1["destination"],
                                            'estimated_savings': 0.4  # Approx 40% cost savings
                                        }
                                        
                                        optimized_assignments.append(shared_assignment)
                                        break
        
        return optimized_assignments
    
    def export_transportation_schedule(self, filename: str):
        """Export all transportation arrangements to a CSV file"""
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['Speaker', 'Meeting', 'Date', 'Type', 'Pickup', 
                         'Destination', 'DateTime', 'Provider', 'Status', 'EstimatedCost']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for speaker_id, speaker in self.speakers.items():
                for i, transport in enumerate(speaker.transportation_needs):
                    meeting_info = ""
                    meeting_date = ""
                    if speaker.meetings:
                        for m in speaker.meetings:
                            meeting_id = m["meeting_id"]
                            if meeting_id in self.meetings:
                                meeting_info = self.meetings[meeting_id].title
                                meeting_date = self.meetings[meeting_id].date.strftime("%Y-%m-%d")
                                break
                    
                    provider_name = ""
                    estimated_cost = ""
                    if "provider_id" in transport:
                        provider_id = transport["provider_id"]
                        if 1 <= provider_id <= len(self.transportation_providers):
                            provider = self.transportation_providers[provider_id-1]
                            provider_name = provider.name
                            
                            # Calculate cost if coordinates are available
                            if transport["coordinates"]["pickup"] and transport["coordinates"]["destination"]:
                                distance = self.calculate_distance(
                                    transport["coordinates"]["pickup"],
                                    transport["coordinates"]["destination"]
                                )
                                if distance:
                                    estimated_cost = f"${provider.estimate_cost(distance):.2f}"
                    
                    writer.writerow({
                        'Speaker': speaker.name,
                        'Meeting': meeting_info,
                        'Date': meeting_date,
                        'Type': transport["type"],
                        'Pickup': transport["pickup"],
                        'Destination': transport["destination"],
                        'DateTime': transport["datetime"].strftime("%Y-%m-%d %H:%M"),
                        'Provider': provider_name,
                        'Status': transport["status"],
                        'EstimatedCost': estimated_cost
                    })
    
    def export_speaker_schedule(self, filename: str):
        """Export speaker schedules to a CSV file"""
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['Speaker', 'Email', 'Phone', 'Meeting', 'Date', 'Location', 'Role', 'Specialization']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for speaker_id, speaker in self.speakers.items():
                for meeting_info in speaker.meetings:
                    meeting_id = meeting_info["meeting_id"]
                    if meeting_id in self.meetings:
                        meeting = self.meetings[meeting_id]
                        writer.writerow({
                            'Speaker': speaker.name,
                            'Email': speaker.email,
                            'Phone': speaker.phone,
                            'Meeting': meeting.title,
                            'Date': meeting.date.strftime("%Y-%m-%d %H:%M"),
                            'Location': meeting.location,
                            'Role': meeting_info["role"],
                            'Specialization': speaker.specialization
                        })
    
    def generate_analytics(self, output_folder='analytics'):
        """Generate analytics visualizations and reports"""
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # 1. Speaker distribution by specialization
        specializations = {}
        for speaker in self.speakers.values():
            if speaker.specialization:
                if speaker.specialization not in specializations:
                    specializations[speaker.specialization] = 0
                specializations[speaker.specialization] += 1
        
        if specializations:
            plt.figure(figsize=(10, 6))
            plt.bar(specializations.keys(), specializations.values())
            plt.title('Speaker Distribution by Specialization')
            plt.xlabel('Specialization')
            plt.ylabel('Number of Speakers')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(f"{output_folder}/speaker_specializations.png")
            plt.close()
        
        # 2. Meeting counts by month
        meeting_months = {}
        for meeting in self.meetings.values():
            month_key = meeting.date.strftime("%Y-%m")
            if month_key not in meeting_months:
                meeting_months[month_key] = 0
            meeting_months[month_key] += 1
        
        if meeting_months:
            sorted_months = sorted(meeting_months.keys())
            plt.figure(figsize=(10, 6))
            plt.plot(sorted_months, [meeting_months[m] for m in sorted_months], marker='o')
            plt.title('Meeting Count by Month')
            plt.xlabel('Month')
            plt.ylabel('Number of Meetings')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(f"{output_folder}/meetings_by_month.png")
            plt.close()
        
        # 3. Transportation provider utilization
        provider_names = [p.name for p in self.transportation_providers]
        utilization = [p.calculate_capacity_utilization() for p in self.transportation_providers]
        
        if provider_names:
            plt.figure(figsize=(10, 6))
            plt.bar(provider_names, utilization)
            plt.title('Transportation Provider Utilization')
            plt.xlabel('Provider')
            plt.ylabel('Utilization (%)')
            plt.axhline(y=80, color='r', linestyle='--', label='High Utilization Threshold')
            plt.legend()
            plt.tight_layout()
            plt.savefig(f"{output_folder}/provider_utilization.png")
            plt.close()
        
        # 4. Speaker clusters visualization (if available)
        if self.speaker_clusters:
            speaker_data = []
            
            for speaker_id, speaker in self.speakers.items():
                features = [
                    speaker.past_events,
                    speaker.rating if speaker.rating else 0,
                    len(speaker.meetings),
                    len(speaker.transportation_needs)
                ]
                speaker_data.append(features)
            
            if speaker_data:
                X = np.array(speaker_data)
                X_scaled = self.speaker_clusters['scaler'].transform(X)
                clusters = self.speaker_clusters['model'].predict(X_scaled)
                
                # Use PCA to reduce to 2D for visualization
                from sklearn.decomposition import PCA
                pca = PCA(n_components=2)
                X_pca = pca.fit_transform(X_scaled)
                
                plt.figure(figsize=(10, 8))
                
                # Plot points
                for i, cluster_id in enumerate(set(clusters)):
                    cluster_points = X_pca[clusters == cluster_id]
                    plt.scatter(
                        cluster_points[:, 0], 
                        cluster_points[:, 1], 
                        label=f'Cluster {cluster_id+1}',
                        alpha=0.7
                    )
                
                plt.title('Speaker Clusters Visualization (PCA)')
                plt.xlabel('Component 1')
                plt.ylabel('Component 2')
                plt.legend()
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.tight_layout()
                plt.savefig(f"{output_folder}/speaker_clusters.png")
                plt.close()
        
        # 5. Generate summary report
        with open(f"{output_folder}/summary_report.txt", 'w') as f:
            f.write("SPEAKER MANAGEMENT SYSTEM - SUMMARY REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Total Speakers: {len(self.speakers)}\n")
            f.write(f"Total Meetings: {len(self.meetings)}\n")
            f.write(f"Total Transportation Providers: {len(self.transportation_providers)}\n\n")
            
            # Speaker statistics
            if self.speakers:
                avg_rating = 0
                count_with_rating = 0
                
                for speaker in self.speakers.values():
                    if speaker.rating:
                        avg_rating += speaker.rating
                        count_with_rating += 1
                
                if count_with_rating > 0:
                    avg_rating /= count_with_rating
                
                f.write(f"Average Speaker Rating: {avg_rating:.2f}/5.0\n")
                f.write(f"Top Specializations: {', '.join(list(specializations.keys())[:3])}\n\n")
            
            # Meeting statistics
            if self.meetings:
                upcoming_meetings = 0
                for meeting in self.meetings.values():
                    if meeting.date > datetime.datetime.now():
                        upcoming_meetings += 1
                
                f.write(f"Upcoming Meetings: {upcoming_meetings}\n")
                
                avg_speakers_per_meeting = sum(len(m.speakers) for m in self.meetings.values()) / len(self.meetings)
                f.write(f"Average Speakers per Meeting: {avg_speakers_per_meeting:.2f}\n\n")
            
            # Transportation statistics
            total_transports = 0
            pending_transports = 0
            
            for speaker in self.speakers.values():
                total_transports += len(speaker.transportation_needs)
                pending_transports += sum(1 for t in speaker.transportation_needs if t["status"] == "Pending")
            
            f.write(f"Total Transportation Requests: {total_transports}\n")
            f.write(f"Pending Transportation Requests: {pending_transports}\n")
            
            if self.transportation_providers:
                avg_reliability = sum(p.reliability_score for p in self.transportation_providers) / len(self.transportation_providers)
                f.write(f"Average Provider Reliability: {avg_reliability:.2f}/5.0\n")
        
        return f"Analytics generated in '{output_folder}' folder"
    
    def save_model(self, filename='speaker_management_models.pkl'):
        """Save trained models for future use"""
        models = {
            'speaker_clusters': self.speaker_clusters,
            'transport_predictor': self.transport_predictor,
            'speaker_vectorizer': self.speaker_vectorizer
        }
        joblib.dump(models, filename)
        return f"Models saved to {filename}"
    
    def load_model(self, filename='speaker_management_models.pkl'):
        """Load trained models"""
        if os.path.exists(filename):
            models = joblib.load(filename)
            self.speaker_clusters = models.get('speaker_clusters')
            self.transport_predictor = models.get('transport_predictor')
            self.speaker_vectorizer = models.get('speaker_vectorizer')
            return True
        return False
    
    def save_data(self, speakers_file='speakers.csv', meetings_file='meetings.csv', providers_file='providers.csv'):
        """Save all data to CSV files"""
        # Save speakers
        with open(speakers_file, 'w', newline='') as csvfile:
            fieldnames = ['ID', 'Name', 'Email', 'Phone', 'Organization', 'Specialization', 
                         'Bio', 'Rating', 'PastEvents']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for speaker_id, speaker in self.speakers.items():
                writer.writerow({
                    'ID': speaker.id,
                    'Name': speaker.name,
                    'Email': speaker.email,
                    'Phone': speaker.phone,
                    'Organization': speaker.organization,
                    'Specialization': speaker.specialization,
                    'Bio': speaker.bio,
                    'Rating': speaker.rating if speaker.rating else '',
                    'PastEvents': speaker.past_events
                })
        
        # Save meetings
        with open(meetings_file, 'w', newline='') as csvfile:
            fieldnames = ['ID', 'Title', 'Date', 'Location', 'Duration', 'MaxSpeakers', 'Importance']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for meeting_id, meeting in self.meetings.items():
                writer.writerow({
                    'ID': meeting.id,
                    'Title': meeting.title,
                    'Date': meeting.date.strftime("%Y-%m-%d %H:%M"),
                    'Location': meeting.location,
                    'Duration': meeting.duration_minutes,
                    'MaxSpeakers': meeting.max_speakers if meeting.max_speakers else '',
                    'Importance': meeting.importance
                })
        
        # Save providers
        with open(providers_file, 'w', newline='') as csvfile:
            fieldnames = ['ID', 'Name', 'Contact', 'TransportTypes', 'MaxCapacity', 
                         'CostPerKm', 'BaseCost', 'ReliabilityScore']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for provider in self.transportation_providers:
                writer.writerow({
                    'ID': provider.id,
                    'Name': provider.name,
                    'Contact': provider.contact,
                    'TransportTypes': ','.join(provider.transport_types),
                    'MaxCapacity': provider.max_capacity,
                    'CostPerKm': provider.cost_per_km,
                    'BaseCost': provider.base_cost,
                    'ReliabilityScore': provider.reliability_score
                })
        
        return f"Data saved to {speakers_file}, {meetings_file}, and {providers_file}"
    
    def load_data(self, speakers_file='speakers.csv', meetings_file='meetings.csv', providers_file='providers.csv'):
        """Load data from CSV files"""
        # Load speakers
        if os.path.exists(speakers_file):
            with open(speakers_file, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    speaker = Speaker(
                        id=row['ID'],
                        name=row['Name'],
                        email=row['Email'],
                        phone=row['Phone'],
                        organization=row['Organization'],
                        specialization=row['Specialization'],
                        bio=row['Bio'],
                        rating=float(row['Rating']) if row['Rating'] else None,
                        past_events=int(row['PastEvents']) if row['PastEvents'] else 0
                    )
                    self.speakers[speaker.id] = speaker
        
        # Load meetings
        if os.path.exists(meetings_file):
            with open(meetings_file, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    meeting = Meeting(
                        id=row['ID'],
                        title=row['Title'],
                        date=datetime.datetime.strptime(row['Date'], "%Y-%m-%d %H:%M"),
                        location=row['Location'],
                        duration_minutes=int(row['Duration']),
                        max_speakers=int(row['MaxSpeakers']) if row['MaxSpeakers'] else None,
                        importance=int(row['Importance'])
                    )
                    self.meetings[meeting.id] = meeting
        
        # Load providers
        if os.path.exists(providers_file):
            with open(providers_file, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    provider = TransportationProvider(
                        id=int(row['ID']),
                        name=row['Name'],
                        contact=row['Contact'],
                        transport_types=row['TransportTypes'].split(','),
                        max_capacity=int(row['MaxCapacity']),
                        cost_per_km=float(row['CostPerKm']),
                        base_cost=float(row['BaseCost']),
                        reliability_score=float(row['ReliabilityScore'])
                    )
                    self.transportation_providers.append(provider)
        
        return (f"Loaded {len(self.speakers)} speakers, {len(self.meetings)} meetings, "
               f"and {len(self.transportation_providers)} providers")


# Example usage:
def main():
    # Initialize the system
    system = SpeakerManagementSystem()
    
    # Add speakers with more attributes
    speaker1 = Speaker(
        "S001", "Jane Doe", "jane@example.com", "555-1234", 
        "Tech Company", "AI", "Expert in artificial intelligence and machine learning.",
        rating=4.8, past_events=12
    )
    speaker2 = Speaker(
        "S002", "John Smith", "john@example.com", "555-5678", 
        "University", "Economics", "Professor of Economics with focus on global markets.",
        rating=4.5, past_events=8
    )
    speaker3 = Speaker(
        "S003", "Alice Johnson", "alice@example.com", "555-9012", 
        "Research Institute", "AI", "Specialist in natural language processing.",
        rating=4.2, past_events=5
    )
    system.add_speaker(speaker1)
    system.add_speaker(speaker2)
    system.add_speaker(speaker3)
    
    # Add meetings with more attributes
    meeting1 = Meeting(
        "M001", "AI Conference", 
        datetime.datetime(2025, 4, 15, 10, 0), 
        "Main Hall, Tech Center, New York", 
        120,
        max_speakers=5,
        topic_keywords=["artificial intelligence", "machine learning", "neural networks"],
        importance=1
    )
    meeting2 = Meeting(
        "M002", "Economic Forum", 
        datetime.datetime(2025, 4, 16, 14, 0), 
        "Room 201, Business Center, Chicago", 
        90,
        max_speakers=3,
        topic_keywords=["economics", "global markets", "finance"],
        importance=2
    )
    meeting3 = Meeting(
        "M003", "Tech Innovation Summit", 
        datetime.datetime(2025, 4, 20, 9, 0), 
        "Innovation Hub, San Francisco", 
        180,
        max_speakers=8,
        topic_keywords=["innovation", "technology", "AI", "future tech"],
        importance=1
    )
    system.add_meeting(meeting1)
    system.add_meeting(meeting2)
    system.add_meeting(meeting3)
    
    # Add availability for speakers
    speaker1.add_availability(
        datetime.datetime(2025, 4, 14, 8, 0),
        datetime.datetime(2025, 4, 18, 20, 0)
    )
    speaker2.add_availability(
        datetime.datetime(2025, 4, 15, 12, 0),
        datetime.datetime(2025, 4, 17, 18, 0)
    )
    
    # Add preferences for speakers
    speaker1.add_preference("hotel", "Grand Hotel")
    speaker1.add_preference("meal", "Vegetarian")
    speaker2.add_preference("hotel", "Business Inn")
    speaker2.add_preference("airport", "ORD")
    
    # Assign speakers to meetings
    meeting1.add_speaker(speaker1.id, "Keynote Speaker")
    meeting1.add_speaker(speaker3.id, "Panelist")
    meeting2.add_speaker(speaker2.id, "Panelist")
    meeting3.add_speaker(speaker1.id, "Workshop Leader")
    
    speaker1.assign_to_meeting(meeting1.id, "Keynote Speaker")
    speaker3.assign_to_meeting(meeting1.id, "Panelist")
    speaker2.assign_to_meeting(meeting2.id, "Panelist")
    speaker1.assign_to_meeting(meeting3.id, "Workshop Leader")
    
    # Add transportation needs
    speaker1.add_transportation_need(
        "Car", 
        "JFK Airport Terminal 2", 
        "Grand Hotel, Manhattan", 
        datetime.datetime(2025, 4, 14, 15, 30),
        "Need space for large luggage",
        priority=1
    )
    speaker2.add_transportation_need(
        "Shuttle", 
        "Union Station, Chicago", 
        "Business Center, Chicago", 
        datetime.datetime(2025, 4, 16, 12, 0),
        priority=2
    )
    speaker3.add_transportation_need(
        "Car", 
        "LaGuardia Airport", 
        "Tech Center, New York", 
        datetime.datetime(2025, 4, 14, 18, 45),
        "Arriving with research equipment",
        priority=2
    )
    
    # Add transportation providers with cost info
    system.add_transportation_provider(
        "City Cabs", 
        "contact@citycabs.com", 
        ["Car", "Van"], 
        4,
        cost_per_km=1.5,
        base_cost=10.0,
        reliability_score=4.2
    )
    system.add_transportation_provider(
        "Conference Shuttle", 
        "shuttle@conference.com", 
        ["Shuttle", "Bus"], 
        20,
        cost_per_km=0.8,
        base_cost=25.0,
        reliability_score=4.5
    )
    system.add_transportation_provider(
        "Executive Cars", 
        "bookings@executivecars.com", 
        ["Car", "Luxury Car"], 
        3,
        cost_per_km=2.2,
        base_cost=15.0,
        reliability_score=4.8
    )
    
    # Update coordinates
    system.update_coordinates()
    
    # Assign transportation (manual)
    system.assign_transportation(speaker1.id, 0, 3)  # Assign Executive Cars to Jane
    system.assign_transportation(speaker2.id, 0, 2)  # Assign Conference Shuttle to John
    
    # Train models
    print("Clustering speakers...")
    speaker_groups = system.cluster_speakers()
    for cluster, speakers in speaker_groups.items():
        print(f"{cluster}: {len(speakers)} speakers")
    
    print("\nAnalyzing speaker clusters...")
    cluster_analysis = system.analyze_speaker_clusters()
    for cluster, stats in cluster_analysis.items():
        print(f"{cluster}: {stats['count']} speakers, Avg rating: {stats['avg_rating']:.2f}")
    
    print("\nVectorizing speakers...")
    system.vectorize_speakers()
    
    print("\nFinding similar speakers to Jane Doe...")
    similar_speakers = system.find_similar_speakers("S001")
    for similar in similar_speakers:
        print(f"- {similar['speaker'].name}: {similar['similarity_score']:.2f} similarity")
    
    print("\nRecommending speakers for AI Conference...")
    recommendations = system.recommend_speakers_for_meeting("M001")
    for rec in recommendations:
        print(f"- {rec['speaker'].name}: {rec['combined_score']:.2f} score")
    
    print("\nOptimizing transportation schedule...")
    optimized = system.optimize_transportation_schedule()
    for opt in optimized:
        print(f"Shared ride with {len(opt['transports'])} speakers using {opt['provider'].name}")
    
    # Generate analytics
    print("\nGenerating analytics...")
    system.generate_analytics()
    
    # Export schedules
    system.export_transportation_schedule("transportation_schedule.csv")
    system.export_speaker_schedule("speaker_schedule.csv")
    
    # Save data and models
    system.save_data()
    system.save_model()
    
    print("\nSpeaker management system initialized and analyzed successfully!")


if __name__ == "__main__":
    main()
